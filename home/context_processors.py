from users.forms import RequestForm


def global_context(request):
    return {
        'contact_form': RequestForm(),
    }