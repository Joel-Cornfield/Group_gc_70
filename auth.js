document.addEventListener('DOMContentLoaded', function() {
    // Handle tab switching from links at bottom of form
    document.getElementById('showSignup').addEventListener('click', function(e) {
        e.preventDefault();
        document.getElementById('signup-tab').click();
    });
    
    document.getElementById('showLogin').addEventListener('click', function(e) {
        e.preventDefault();
        document.getElementById('login-tab').click();
    });
});