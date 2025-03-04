
def track_logged_in(sender, user):
    """ This function is executed everytime CKAN core
        sends the logged_in signal.
        This signals comes from Flask-Login.

        Sender <CKANFlask 'ckan.config.middleware.flask_app'>
        User <User id=c3987980 ...> logged in

    """
    pass


def track_logged_out(sender, user):
    """ This function is executed everytime CKAN core
        sends the logged_out signal.
        This signals comes from Flask-Login.
    """
    pass
