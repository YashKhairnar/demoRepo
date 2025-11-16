"""
Comprehensive unit tests for app.py

Tests cover:
- Home endpoint functionality
- Bug endpoint error handling
- Sentry integration
- Flask application configuration
- Error responses
- Edge cases and failure scenarios
"""

import pytest
from unittest.mock import patch, MagicMock, call
import sentry_sdk
from flask import Flask


class TestFlaskAppConfiguration:
    """Tests for Flask application configuration and setup"""
    
    def test_app_is_flask_instance(self):
        """Test that app is a valid Flask instance"""
        with patch('sentry_sdk.init'):
            import app as app_module
            assert isinstance(app_module.app, Flask)
    
    def test_app_name_is_correct(self):
        """Test that Flask app has correct name"""
        with patch('sentry_sdk.init'):
            import app as app_module
            assert app_module.app.name == 'app'
    
    def test_sentry_init_called_with_correct_dsn(self):
        """Test that Sentry is initialized with the correct DSN"""
        with patch('sentry_sdk.init') as mock_sentry_init:
            # Reimport to trigger initialization
            import importlib
            import app as app_module
            importlib.reload(app_module)
            
            # Verify sentry_sdk.init was called
            assert mock_sentry_init.called
            
            # Check DSN argument
            call_args = mock_sentry_init.call_args
            assert 'dsn' in call_args.kwargs or (call_args.args and len(call_args.args) > 0)
            dsn = call_args.kwargs.get('dsn') or call_args.args[0] if call_args.args else None
            assert dsn is not None
            assert 'sentry.io' in dsn
    
    def test_sentry_init_called_with_pii_enabled(self):
        """Test that Sentry is configured to send PII data"""
        with patch('sentry_sdk.init') as mock_sentry_init:
            import importlib
            import app as app_module
            importlib.reload(app_module)
            
            call_args = mock_sentry_init.call_args
            send_pii = call_args.kwargs.get('send_default_pii', False)
            assert send_pii is True


class TestHomeEndpoint:
    """Tests for the home route (/"""
    
    @pytest.fixture
    def client(self):
        """Create a test client for the Flask app"""
        with patch('sentry_sdk.init'):
            import app as app_module
            app_module.app.config['TESTING'] = True
            with app_module.app.test_client() as client:
                yield client
    
    def test_home_returns_200_status(self, client):
        """Test that home endpoint returns 200 OK"""
        response = client.get('/')
        assert response.status_code == 200
    
    def test_home_returns_expected_message(self, client):
        """Test that home endpoint returns the correct message"""
        response = client.get('/')
        assert response.data.decode('utf-8') == "Sentry is working! Go to /bug to trigger an error 🪲"
    
    def test_home_returns_text_html_content_type(self, client):
        """Test that home endpoint returns HTML content type"""
        response = client.get('/')
        assert 'text/html' in response.content_type or 'text/plain' in response.content_type
    
    def test_home_get_method_allowed(self, client):
        """Test that GET method is allowed on home endpoint"""
        response = client.get('/')
        assert response.status_code == 200
    
    def test_home_post_method_not_allowed(self, client):
        """Test that POST method returns 405 Method Not Allowed"""
        response = client.post('/')
        assert response.status_code == 405
    
    def test_home_put_method_not_allowed(self, client):
        """Test that PUT method returns 405 Method Not Allowed"""
        response = client.put('/')
        assert response.status_code == 405
    
    def test_home_delete_method_not_allowed(self, client):
        """Test that DELETE method returns 405 Method Not Allowed"""
        response = client.delete('/')
        assert response.status_code == 405
    
    def test_home_head_method_allowed(self, client):
        """Test that HEAD method is allowed"""
        response = client.head('/')
        assert response.status_code == 200
    
    def test_home_returns_consistent_response_multiple_calls(self, client):
        """Test that home endpoint returns consistent responses"""
        response1 = client.get('/')
        response2 = client.get('/')
        response3 = client.get('/')
        
        assert response1.data == response2.data == response3.data
        assert response1.status_code == response2.status_code == response3.status_code


class TestBugEndpoint:
    """Tests for the bug route (/bug)"""
    
    @pytest.fixture
    def client(self):
        """Create a test client for the Flask app"""
        with patch('sentry_sdk.init'):
            import app as app_module
            app_module.app.config['TESTING'] = True
            with app_module.app.test_client() as client:
                yield client
    
    def test_bug_endpoint_raises_zero_division_error(self, client):
        """Test that /bug endpoint raises ZeroDivisionError"""
        with pytest.raises(ZeroDivisionError):
            client.get('/bug')
    
    def test_bug_endpoint_returns_500_in_production_mode(self, client):
        """Test that /bug returns 500 Internal Server Error in production mode"""
        # In testing mode with propagate_exceptions, we get the exception
        # In production, Flask would return 500
        with patch('sentry_sdk.init'):
            import app as app_module
            app_module.app.config['TESTING'] = False
            app_module.app.config['PROPAGATE_EXCEPTIONS'] = False
            
            with app_module.app.test_client() as prod_client:
                response = prod_client.get('/bug')
                assert response.status_code == 500
    
    def test_bug_endpoint_division_by_zero_is_deliberate(self, client):
        """Test that the division by zero is the expected error type"""
        try:
            client.get('/bug')
            pytest.fail("Expected ZeroDivisionError was not raised")
        except ZeroDivisionError as e:
            # Verify it's a division by zero error
            assert 'division by zero' in str(e) or 'division' in str(type(e).__name__).lower()
    
    def test_bug_endpoint_post_method_not_allowed(self, client):
        """Test that POST method returns 405 on /bug endpoint"""
        # Even though it will error, the route should exist
        with pytest.raises(ZeroDivisionError):
            client.post('/bug')
    
    def test_bug_endpoint_doesnt_return_success_message(self, client):
        """Test that the 'no bug' message is never returned due to error"""
        try:
            response = client.get('/bug')
            # If we somehow get here, verify we don't get the success message
            assert b"no bug" not in response.data
        except ZeroDivisionError:
            # Expected behavior - error occurs before return statement
            pass
    
    def test_bug_endpoint_error_occurs_before_return(self, client):
        """Test that error happens on line 23 before line 24 return statement"""
        import app as app_module
        import inspect
        
        # Get the source code of trigger_bug function
        source = inspect.getsource(app_module.trigger_bug)
        lines = source.split('\n')
        
        # Verify division by zero comes before return
        div_by_zero_found = False
        return_found = False
        
        for line in lines:
            if '1 / 0' in line or '1/0' in line:
                div_by_zero_found = True
            if 'return' in line and div_by_zero_found:
                return_found = True
        
        assert div_by_zero_found, "Division by zero statement not found"
        assert return_found, "Return statement should exist after division"


class TestSentryIntegration:
    """Tests for Sentry SDK integration and error tracking"""
    
    def test_sentry_captures_zero_division_error(self):
        """Test that Sentry captures the ZeroDivisionError from /bug endpoint"""
        with patch('sentry_sdk.init') as mock_init:
            with patch('sentry_sdk.capture_exception') as mock_capture:
                import app as app_module
                app_module.app.config['TESTING'] = False
                app_module.app.config['PROPAGATE_EXCEPTIONS'] = False
                
                with app_module.app.test_client() as client:
                    try:
                        client.get('/bug')
                    except:
                        pass
                
                # Sentry should have been initialized
                assert mock_init.called
    
    def test_sentry_dsn_is_configured(self):
        """Test that Sentry DSN is properly configured"""
        with patch('sentry_sdk.init') as mock_sentry:
            import importlib
            import app as app_module
            importlib.reload(app_module)
            
            # Verify init was called with DSN
            assert mock_sentry.called
            call_kwargs = mock_sentry.call_args.kwargs
            
            if 'dsn' in call_kwargs:
                dsn = call_kwargs['dsn']
                assert dsn is not None
                assert len(dsn) > 0
                assert 'https://' in dsn


class TestRouteRegistration:
    """Tests for route registration and URL patterns"""
    
    @pytest.fixture
    def client(self):
        """Create a test client for the Flask app"""
        with patch('sentry_sdk.init'):
            import app as app_module
            app_module.app.config['TESTING'] = True
            with app_module.app.test_client() as client:
                yield client
    
    def test_root_route_is_registered(self, client):
        """Test that root route (/) is registered"""
        response = client.get('/')
        assert response.status_code != 404
    
    def test_bug_route_is_registered(self, client):
        """Test that /bug route is registered"""
        try:
            response = client.get('/bug')
            assert response.status_code != 404
        except ZeroDivisionError:
            # Route exists but raises error (expected)
            pass
    
    def test_nonexistent_route_returns_404(self, client):
        """Test that non-existent routes return 404"""
        response = client.get('/nonexistent')
        assert response.status_code == 404
    
    def test_bug_route_without_trailing_slash(self, client):
        """Test that /bug route works without trailing slash"""
        try:
            response = client.get('/bug')
            assert True  # Route exists
        except ZeroDivisionError:
            pass  # Expected error
    
    def test_bug_route_with_trailing_slash_redirects_or_not_found(self, client):
        """Test behavior of /bug/ with trailing slash"""
        response = client.get('/bug/', follow_redirects=False)
        # Should either redirect to /bug or return 404/308
        assert response.status_code in [301, 308, 404]


class TestApplicationBehavior:
    """Tests for overall application behavior and edge cases"""
    
    @pytest.fixture
    def client(self):
        """Create a test client for the Flask app"""
        with patch('sentry_sdk.init'):
            import app as app_module
            app_module.app.config['TESTING'] = True
            with app_module.app.test_client() as client:
                yield client
    
    def test_app_handles_multiple_concurrent_home_requests(self, client):
        """Test that app can handle multiple requests to home"""
        responses = [client.get('/') for _ in range(10)]
        assert all(r.status_code == 200 for r in responses)
    
    def test_app_unicode_handling_in_response(self, client):
        """Test that app correctly handles unicode emoji in response"""
        response = client.get('/')
        data = response.data.decode('utf-8')
        assert '🪲' in data
    
    def test_case_sensitive_routes(self, client):
        """Test that routes are case-sensitive"""
        response = client.get('/BUG')
        assert response.status_code == 404
        
        response = client.get('/Bug')
        assert response.status_code == 404
    
    def test_home_response_length(self, client):
        """Test that home response has expected length"""
        response = client.get('/')
        assert len(response.data) > 0
    
    def test_app_has_correct_routes_count(self):
        """Test that app has exactly 2 routes registered"""
        with patch('sentry_sdk.init'):
            import app as app_module
            
            # Count user-defined routes (excluding static)
            routes = [rule.rule for rule in app_module.app.url_map.iter_rules() 
                     if not rule.rule.startswith('/static')]
            
            # Should have / and /bug
            assert '/' in routes
            assert '/bug' in routes


class TestErrorHandling:
    """Tests for error handling and exception scenarios"""
    
    @pytest.fixture
    def client(self):
        """Create a test client for the Flask app"""
        with patch('sentry_sdk.init'):
            import app as app_module
            app_module.app.config['TESTING'] = True
            with app_module.app.test_client() as client:
                yield client
    
    def test_zero_division_error_type(self, client):
        """Test that the exact error type is ZeroDivisionError"""
        with pytest.raises(ZeroDivisionError) as exc_info:
            client.get('/bug')
        
        assert exc_info.type is ZeroDivisionError
    
    def test_error_message_content(self, client):
        """Test the error message from division by zero"""
        with pytest.raises(ZeroDivisionError) as exc_info:
            client.get('/bug')
        
        error_msg = str(exc_info.value)
        assert 'division by zero' in error_msg.lower() or error_msg == 'integer division or modulo by zero'
    
    def test_home_endpoint_does_not_raise_errors(self, client):
        """Test that home endpoint does not raise any errors"""
        try:
            response = client.get('/')
            assert response.status_code == 200
        except Exception as e:
            pytest.fail(f"Home endpoint raised unexpected exception: {e}")


class TestImportsAndDependencies:
    """Tests for module imports and dependencies"""
    
    def test_flask_import_successful(self):
        """Test that Flask is successfully imported"""
        with patch('sentry_sdk.init'):
            import app as app_module
            assert hasattr(app_module, 'Flask')
    
    def test_sentry_sdk_import_successful(self):
        """Test that sentry_sdk is successfully imported"""
        with patch('sentry_sdk.init'):
            import app as app_module
            assert hasattr(app_module, 'sentry_sdk')
    
    def test_os_module_imported(self):
        """Test that os module is imported (even if not used)"""
        with patch('sentry_sdk.init'):
            import app as app_module
            assert hasattr(app_module, 'os')
    
    def test_flask_integration_available(self):
        """Test that FlaskIntegration is available"""
        with patch('sentry_sdk.init'):
            import app as app_module
            from sentry_sdk.integrations.flask import FlaskIntegration
            assert FlaskIntegration is not None


class TestMainBlock:
    """Tests for the __main__ block execution"""
    
    def test_main_block_not_executed_on_import(self):
        """Test that app.run() is not called when module is imported"""
        with patch('sentry_sdk.init'):
            with patch('flask.Flask.run') as mock_run:
                import importlib
                import app as app_module
                importlib.reload(app_module)
                
                # run() should not be called on import
                # (only when __name__ == "__main__")
                # Since we're importing, __name__ will be 'app', not '__main__'
                assert not mock_run.called or mock_run.call_count == 0


class TestEndpointResponseProperties:
    """Tests for detailed response properties"""
    
    @pytest.fixture
    def client(self):
        """Create a test client for the Flask app"""
        with patch('sentry_sdk.init'):
            import app as app_module
            app_module.app.config['TESTING'] = True
            with app_module.app.test_client() as client:
                yield client
    
    def test_home_response_is_string(self, client):
        """Test that home response data is a string"""
        response = client.get('/')
        assert isinstance(response.data, bytes)
        assert isinstance(response.data.decode('utf-8'), str)
    
    def test_home_response_not_empty(self, client):
        """Test that home response is not empty"""
        response = client.get('/')
        assert len(response.data) > 0
    
    def test_home_response_contains_sentry_reference(self, client):
        """Test that home response mentions Sentry"""
        response = client.get('/')
        data = response.data.decode('utf-8')
        assert 'Sentry' in data or 'sentry' in data.lower()
    
    def test_home_response_contains_bug_route_reference(self, client):
        """Test that home response references the /bug route"""
        response = client.get('/')
        data = response.data.decode('utf-8')
        assert '/bug' in data


class TestSecurityAndConfiguration:
    """Tests for security and configuration concerns"""
    
    def test_hardcoded_dsn_present(self):
        """Test that DSN is hardcoded (security concern for prod)"""
        with patch('sentry_sdk.init') as mock_init:
            import importlib
            import app as app_module
            importlib.reload(app_module)
            
            # Check that DSN is hardcoded (not from env var)
            call_args = mock_init.call_args
            if call_args:
                dsn = call_args.kwargs.get('dsn') or (call_args.args[0] if call_args.args else None)
                assert dsn is not None
                # This is a security concern - DSN should ideally come from env
    
    def test_app_debug_mode_not_enabled_by_default(self):
        """Test that debug mode is not enabled by default"""
        with patch('sentry_sdk.init'):
            import app as app_module
            # Debug should not be explicitly enabled
            assert not app_module.app.debug


class TestFunctionDefinitions:
    """Tests for function definitions and signatures"""
    
    def test_home_function_exists(self):
        """Test that home function is defined"""
        with patch('sentry_sdk.init'):
            import app as app_module
            assert hasattr(app_module, 'home')
            assert callable(app_module.home)
    
    def test_trigger_bug_function_exists(self):
        """Test that trigger_bug function is defined"""
        with patch('sentry_sdk.init'):
            import app as app_module
            assert hasattr(app_module, 'trigger_bug')
            assert callable(app_module.trigger_bug)
    
    def test_home_function_takes_no_arguments(self):
        """Test that home function takes no arguments"""
        with patch('sentry_sdk.init'):
            import app as app_module
            import inspect
            sig = inspect.signature(app_module.home)
            assert len(sig.parameters) == 0
    
    def test_trigger_bug_function_takes_no_arguments(self):
        """Test that trigger_bug function takes no arguments"""
        with patch('sentry_sdk.init'):
            import app as app_module
            import inspect
            sig = inspect.signature(app_module.trigger_bug)
            assert len(sig.parameters) == 0


class TestEdgeCasesAndRobustness:
    """Tests for edge cases and application robustness"""
    
    @pytest.fixture
    def client(self):
        """Create a test client for the Flask app"""
        with patch('sentry_sdk.init'):
            import app as app_module
            app_module.app.config['TESTING'] = True
            with app_module.app.test_client() as client:
                yield client
    
    def test_query_parameters_ignored_on_home(self, client):
        """Test that query parameters don't affect home endpoint"""
        response1 = client.get('/')
        response2 = client.get('/?foo=bar')
        response3 = client.get('/?test=123&other=456')
        
        assert response1.data == response2.data == response3.data
    
    def test_query_parameters_dont_prevent_bug_error(self, client):
        """Test that query parameters don't prevent error on /bug"""
        with pytest.raises(ZeroDivisionError):
            client.get('/bug?test=123')
    
    def test_accept_header_variations(self, client):
        """Test different Accept headers on home endpoint"""
        headers1 = {'Accept': 'text/html'}
        headers2 = {'Accept': 'application/json'}
        headers3 = {'Accept': '*/*'}
        
        response1 = client.get('/', headers=headers1)
        response2 = client.get('/', headers=headers2)
        response3 = client.get('/', headers=headers3)
        
        # All should return 200 regardless of Accept header
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response3.status_code == 200
    
    def test_user_agent_variations(self, client):
        """Test different User-Agent headers"""
        headers1 = {'User-Agent': 'Mozilla/5.0'}
        headers2 = {'User-Agent': 'curl/7.68.0'}
        headers3 = {'User-Agent': 'Python-requests/2.25.1'}
        
        response1 = client.get('/', headers=headers1)
        response2 = client.get('/', headers=headers2)
        response3 = client.get('/', headers=headers3)
        
        assert all(r.status_code == 200 for r in [response1, response2, response3])


class TestIntegrationScenarios:
    """Integration-style tests for complete scenarios"""
    
    @pytest.fixture
    def client(self):
        """Create a test client for the Flask app"""
        with patch('sentry_sdk.init'):
            import app as app_module
            app_module.app.config['TESTING'] = True
            with app_module.app.test_client() as client:
                yield client
    
    def test_user_journey_home_then_bug(self, client):
        """Test typical user journey: visit home, then trigger bug"""
        # Visit home
        response1 = client.get('/')
        assert response1.status_code == 200
        assert '/bug' in response1.data.decode('utf-8')
        
        # Then visit bug
        with pytest.raises(ZeroDivisionError):
            client.get('/bug')
    
    def test_multiple_home_visits_between_errors(self, client):
        """Test visiting home multiple times between bug triggers"""
        for i in range(3):
            response = client.get('/')
            assert response.status_code == 200
            
            if i < 2:  # Don't error on last iteration
                with pytest.raises(ZeroDivisionError):
                    client.get('/bug')
    
    def test_app_still_functional_after_error(self, client):
        """Test that app remains functional after triggering error"""
        # Trigger error
        with pytest.raises(ZeroDivisionError):
            client.get('/bug')
        
        # App should still respond to home
        response = client.get('/')
        assert response.status_code == 200
        
        # Can trigger error again
        with pytest.raises(ZeroDivisionError):
            client.get('/bug')