from django.contrib.auth.mixins import UserPassesTestMixin


class AdminRequiredMixin(UserPassesTestMixin):
    """Solo administradores (rol admin o superuser)."""

    def test_func(self):
        return self.request.user.es_admin
