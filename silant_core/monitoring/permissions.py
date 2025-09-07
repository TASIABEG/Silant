from rest_framework import permissions

class IsClient(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'client'

class IsService(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'service'

class IsManager(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'manager'

class ClientOrServicePermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role in ['client', 'service']