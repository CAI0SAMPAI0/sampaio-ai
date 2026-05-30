from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.views import generic
from django.contrib.auth.models import User
from django.db import DatabaseError
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .models import UserProfile


class RegisterView(generic.CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'registration/register.html'


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    username = request.data.get('username')
    password = request.data.get('password')

    if not username or not password:
        return Response({'error': 'Username and password are required.'}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=username).exists():
        return Response({'error': 'Username already exists.'}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(username=username, password=password)
    refresh = RefreshToken.for_user(user)

    return Response({
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }, status=status.HTTP_201_CREATED)


def build_avatar_url(request, profile):
    if not profile or not profile.avatar:
        return None

    try:
        return request.build_absolute_uri(profile.avatar.url)
    except Exception:
        return None


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile(request):
    user = request.user
    profile_obj = None

    try:
        profile_obj, _ = UserProfile.objects.get_or_create(user=user)
    except DatabaseError:
        # Do not fail the whole authenticated session if the optional profile
        # table/storage is temporarily unavailable; the frontend can still load
        # the user identity and continue without an avatar.
        profile_obj = None

    return Response({
        'id': user.id,
        'username': user.username,
        'avatar': build_avatar_url(request, profile_obj),
    })


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def update_profile(request):
    user = request.user

    try:
        profile_obj, _ = UserProfile.objects.get_or_create(user=user)
    except DatabaseError:
        return Response({'error': 'Perfil temporariamente indisponível.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    if 'username' in request.data:
        new_username = request.data['username']
        if User.objects.exclude(pk=user.pk).filter(username=new_username).exists():
            return Response({'error': 'Username já em uso.'}, status=400)
        user.username = new_username
        user.save()

    if 'avatar' in request.FILES:
        profile_obj.avatar = request.FILES['avatar']
        try:
            profile_obj.save()
        except Exception:
            return Response({'error': 'Erro ao salvar avatar.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    return Response({
        'username': user.username,
        'avatar': build_avatar_url(request, profile_obj),
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    user = request.user
    current = request.data.get('current_password')
    new = request.data.get('new_password')

    if not user.check_password(current):
        return Response({'error': 'Senha atual incorreta.'}, status=400)
    if not new or len(new) < 6:
        return Response({'error': 'Nova senha muito curta.'}, status=400)

    user.set_password(new)
    user.save()
    return Response({'message': 'Senha alterada com sucesso.'})


@api_view(['POST'])
@permission_classes([AllowAny])
def logout(request):
    if request.method == 'POST':
        try:
            refresh_token = request.data.get('refresh')
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Logout successful.'}, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
