import requests
from loguru import logger
from .models import Contact, Deal
from typing import Union


class BtxClient:

    def __init__(self, btx_webhook: str):

        self.btx_webhook: str = btx_webhook
        logger.add('logs/logs.log', format="{time} {level} {message}")
        self.create_uf()
        logger.info('Starting...')
        # не уверен стоит ли выносить api методы отдельным списком или полями

    def create_uf(self):
        user_fields = [
            {
                'FIELD_NAME': 'DELIVERY_ADDRESS',
                'USER_TYPE_ID': 'string'
            },
            {
                'FIELD_NAME': 'DELIVERY_DATE',
                'USER_TYPE_ID': 'string'
            },
            {
                'FIELD_NAME': 'DELIVERY_CODE',
                'USER_TYPE_ID': 'string'
            }
        ]
        for field in user_fields:
            requests.post(self.btx_webhook + 'crm.deal.userfield.add', field)

    def get_contact_id(self, phone: str) -> Union[str, None]:
        body = {
            'select': ['NAME', 'LAST_NAME', 'PHONE', 'ADDRESS'],
            'filter': {'PHONE': phone}
        }
        response: requests.Response = requests.post(self.btx_webhook + 'crm.contact.list', json=body)
        result = response.json().get('result')
        print(response.json())
        if result:
            return result[0].get('ID')
        else:
            return None

    def get_current_products_by_id(self, deal_id: str) -> list:
        body = {
            'id': deal_id
        }
        response: requests.Response = requests.post(self.btx_webhook + 'crm.deal.productrows.get', json=body)
        result = response.json().get('result')
        current_product = [x.get('PRODUCT_NAME') for x in result]
        # привожу [{'PRODUCT_NAME': 'Product1'}, {'PRODUCT_NAME': 'Product2'}] к виду ['Product1', 'Product2']
        return current_product

    def get_deal_id(self, deal: Deal) -> str:
        body = {
            'select': ['ID'],
            'filter': {'UF_CRM_DELIVERY_CODE': deal.delivery_code}
        }
        response = requests.post(self.btx_webhook + 'crm.deal.list', json=body)
        result = response.json().get('result')
        return result[0].get('ID')

    def get_exist_deal(self, delivery_code: str) -> Union[Deal, None]:
        body = {
            'select': ["ID", "TITLE", 'UF_CRM_DELIVERY_DATE',
                       'UF_CRM_DELIVERY_ADDRESS', 'UF_CRM_DELIVERY_CODE', 'SOURCE_DESCRIPTION'],
            'filter': {'UF_CRM_DELIVERY_CODE': delivery_code}
        }
        response: requests.Response = requests.post(self.btx_webhook + 'crm.deal.list', json=body)
        result = response.json().get('result')
        deal: Deal() = Deal()
        if result:
            deal.title = result[0].get('TITLE')
            deal.description = result[0].get('SOURCE_DESCRIPTION')
            deal.products = self.get_current_products_by_id(result[0].get('ID'))
            deal.delivery_date = result[0].get('UF_CRM_DELIVERY_DATE')
            deal.delivery_address = result[0].get('UF_CRM_DELIVERY_ADDRESS')
            deal.delivery_code = result[0].get('UF_CRM_DELIVERY_CODE')
            return deal

        return None

    def create_contact(self, contact_data: Contact) -> str:
        exist_contact = self.get_contact_id(contact_data.phone)  # Проверяем существует ли контакт
        if exist_contact:
            logger.warning(f'Contact with this phone ({contact_data.phone}) already exist.')
            return exist_contact  # Возвращаем ID чтобы привязать контакт к сделке

        body = {
            'fields': {
                'NAME': contact_data.name,
                'LAST_NAME': contact_data.surname,
                'PHONE': [{"VALUE": contact_data.phone}],
                'ADDRESS': contact_data.address
            }
        }
        response: requests.Response = requests.post(self.btx_webhook + 'crm.contact.add', json=body)
        # Создаем контакт если его не было
        result = response.json().get('result')
        logger.info('New contact is added.')
        return result

    def deal_update(self, new_deal: Deal):
        deal_id = self.get_deal_id(new_deal)
        body = {
            'id': deal_id,
            'fields': {
                'UF_CRM_DELIVERY_ADDRESS': new_deal.delivery_address,
                'UF_CRM_DELIVERY_DATE': new_deal.delivery_date
            }
        }
        requests.Response = requests.post(self.btx_webhook + 'crm.deal.update', json=body)
        new_products = [{'PRODUCT_NAME': x} for x in new_deal.products]
        # приводим лист ['Product1', 'Product2'] к виду [{'PRODUCT_NAME': 'Product1'}, {'PRODUCT_NAME': 'Product2'}]
        # не стал устанавливать цену количество т.к. на входе их нет

        body = {
            'id': deal_id,
            'rows': new_products
        }
        requests.post(self.btx_webhook + 'crm.deal.productrows.set', json=body)

    def create_deal(self, deal_data: Deal, contact_id: str):
        exist_deal = self.get_exist_deal(deal_data.delivery_code)
        if exist_deal:
            if deal_data == exist_deal:  # в данном случае сделал изменения если хотябы одно поле не совпало
                return  # Если сделака существует и поля не поменялись, то ничего не делаем
            self.deal_update(deal_data)  # Обновляем поля, если есть изменения
            return

        body = {
            'fields': {
                'TITLE': deal_data.title,
                'SOURCE_DESCRIPTION': deal_data.description,
                'UF_CRM_DELIVERY_ADDRESS': deal_data.delivery_address,
                'UF_CRM_DELIVERY_DATE': deal_data.delivery_date,
                'UF_CRM_DELIVERY_CODE': deal_data.delivery_code
            }
        }
        requests.post(self.btx_webhook + 'crm.deal.add', json=body)

        deal_id = self.get_deal_id(deal_data)
        self.products_set(deal_id, deal_data)
        self.contact_add(deal_id, contact_id)

    def products_set(self, deal_id: str, deal_data: Deal):
        new_products = [{'PRODUCT_NAME': x} for x in deal_data.products]
        body = {
            'id': deal_id,
            'rows': new_products
        }
        requests.post(self.btx_webhook + 'crm.deal.productrows.set', json=body)

    def contact_add(self, deal_id: str, contact_id: str):
        body = {
            'id': deal_id,
            'fields': {
                'CONTACT_ID': contact_id
            }
        }
        requests.post(self.btx_webhook + 'crm.deal.contact.add', json=body)
