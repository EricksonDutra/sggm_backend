from rest_framework import viewsets

from .models import *
from .serializers import *


class MusicoViewSet(viewsets.ModelViewSet):
    queryset = Musicos.objects.all()
    serializer_class = MusicosSerializer


class EventoViewSet(viewsets.ModelViewSet):
    queryset = Eventos.objects.all()
    serializer_class = EventosSerializer


class EscalaViewSet(viewsets.ModelViewSet):
    queryset = Escalas.objects.all()
    serializer_class = EscalasSerializer


class MusicaViewSet(viewsets.ModelViewSet):
    queryset = Musicas.objects.all()
    serializer_class = MusicasSerializer

class EscalaRepertorioViewSet(viewsets.ModelViewSet):
    queryset = EscalaRepertorio.objects.all()
    serializer_class = EscalasSerializer