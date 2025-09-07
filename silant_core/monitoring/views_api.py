from rest_framework import viewsets, permissions


class MachineViewSet(viewsets.ModelViewSet):
    serializer_class = MachineSerializer

    def get_queryset(self):
        return self.request.user.get_accessible_machines()

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy', 'create']:
            permission_classes = [permissions.IsAuthenticated, ManagerPermission]
        else:
            permission_classes = [permissions.IsAuthenticatedOrReadOnly]
        return [permission() for permission in permission_classes]


class TechnicalServiceViewSet(viewsets.ModelViewSet):
    serializer_class = TechnicalServiceSerializer

    def get_queryset(self):
        return TechnicalService.get_visible_to_user(self.request.user)

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, ServiceOrManagerPermission]
        elif self.action == 'create':
            permission_classes = [permissions.IsAuthenticated, ClientOrServicePermission]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]


class ManagerPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.can_edit_machines()


class ServiceOrManagerPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.can_be_edited_by(request.user)