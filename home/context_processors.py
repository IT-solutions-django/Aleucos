from users.forms import RequestForm, RegistrationRequest


def global_context(request):
    return {
        'contact_form': RegistrationRequest(),
    }