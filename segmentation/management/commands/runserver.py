import time
import webbrowser
import threading
from django.core.management.commands.runserver import Command as RunServerCommand


class Command(RunServerCommand):
    """
    Custom runserver command that automatically opens the dashboard in the browser
    when the development server starts.
    """

    def handle(self, *args, **options):
        """
        Override the default handle method to add browser auto-launch functionality.
        """
        # Determine the server URL
        host = options.get('host', '127.0.0.1')
        port = options.get('port', 8000)
        
        # Handle special host cases
        if host == '0.0.0.0':
            host = 'localhost'
        
        server_url = f'http://{host}:{port}/'
        
        # Launch browser in a separate thread after a brief delay
        def open_browser():
            # Wait for server to start (2-3 seconds)
            time.sleep(2.5)
            try:
                webbrowser.open(server_url)
                self.stdout.write(
                    self.style.SUCCESS(f'\n✓ Browser opened at {server_url}\n')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'\n⚠ Could not open browser automatically: {e}\n')
                )
        
        # Start browser thread as daemon so it doesn't block server shutdown
        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()
        
        # Start the normal runserver
        self.stdout.write(
            self.style.SUCCESS('\nStarting Django development server...\n')
        )
        super().handle(*args, **options)
