from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import ContactSerializer, DealSerializer
# Create your views here.
from rest_framework.request import Request
from .models import Contact, Deal
from .Settings.config import btx_webhook
from .BtxClient import BtxClient


class ContactAPIView(APIView):

    def get(self, r: Request):
        #contacts = Contact.objects.all()
        #print(r.query_params.dict())
        return Response({'test': 'Test get request'})

    def post(self, r: Request):
        contact_serializer = ContactSerializer(data=r.data['client'])
        contact_serializer.is_valid(raise_exception=True)
        contact = Contact(**contact_serializer.data)  # contact_serializer.create(r.data)
        deal_serializer = DealSerializer(data=r.data)
        deal_serializer.is_valid()
        deal = deal_serializer.create(r.data)  # Deal(**r.data)

        client = BtxClient(btx_webhook)
        c_id = client.create_contact(contact)
        client.create_deal(deal, c_id)

        return Response(
            {
                'contact': contact_serializer.data,
                'deal': deal_serializer.data
            }
        )
