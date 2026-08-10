"""Generated typed HTTP operations. Do not edit."""
# ruff: noqa
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, ConfigDict, RootModel

from bastion_ui.transport.foundation import (
    ContractRegistryEntry, HttpTransport, NormalizedOperation, SafeTransportError, SecurityMetadata,
    serialize_query_value,
)
from bastion_ui.transport.generated_schemas import *  # noqa: F403

class NoRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)

class ListChildApiKeysApiV1AccessApiKeysGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    pass

class ListChildApiKeysApiV1AccessApiKeysGetSuccess(RootModel[list[ChildApiKeyPublic]]):
    pass

ListChildApiKeysApiV1AccessApiKeysGetError = SafeTransportError

LISTCHILDAPIKEYSAPIV1ACCESSAPIKEYSGET_SECURITY = SecurityMetadata(
    identity='access-session:list_child_api_keys_api_v1_access_api_keys_get', public=False, access_required=True,
    signed_request_required=False, human_intent_required=False,
    source_symbol='list_child_api_keys_api_v1_access_api_keys_get', review_owner='Stage 1B0-R7',
)
LISTCHILDAPIKEYSAPIV1ACCESSAPIKEYSGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0002', operation_id='list_child_api_keys_api_v1_access_api_keys_get',
    method='GET', path='/api/v1/access/api-keys', backend_tag='proof-of-access',
    product='Access', disposition='UI_REQUIRED',
    success_status=200, response_type=ListChildApiKeysApiV1AccessApiKeysGetSuccess, security=LISTCHILDAPIKEYSAPIV1ACCESSAPIKEYSGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:list_child_api_keys_api_v1_access_api_keys_get',
    response_media_type='application/json',
)
async def list_child_api_keys_api_v1_access_api_keys_get(transport: HttpTransport, request: ListChildApiKeysApiV1AccessApiKeysGetRequest) -> ListChildApiKeysApiV1AccessApiKeysGetSuccess:
    return await transport.invoke(LISTCHILDAPIKEYSAPIV1ACCESSAPIKEYSGET_OPERATION, path_parameters={}, query_parameters={}, body=None)

class GetChildApiKeyApiV1AccessApiKeysKeyIdGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    key_id: str

class GetChildApiKeyApiV1AccessApiKeysKeyIdGetSuccess(RootModel[ChildApiKeyPublic]):
    pass

GetChildApiKeyApiV1AccessApiKeysKeyIdGetError = SafeTransportError

GETCHILDAPIKEYAPIV1ACCESSAPIKEYSKEYIDGET_SECURITY = SecurityMetadata(
    identity='access-session:get_child_api_key_api_v1_access_api_keys__key_id__get', public=False, access_required=True,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_child_api_key_api_v1_access_api_keys__key_id__get', review_owner='Stage 1B0-R7',
)
GETCHILDAPIKEYAPIV1ACCESSAPIKEYSKEYIDGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0005', operation_id='get_child_api_key_api_v1_access_api_keys__key_id__get',
    method='GET', path='/api/v1/access/api-keys/{key_id}', backend_tag='proof-of-access',
    product='Access', disposition='UI_REQUIRED',
    success_status=200, response_type=GetChildApiKeyApiV1AccessApiKeysKeyIdGetSuccess, security=GETCHILDAPIKEYAPIV1ACCESSAPIKEYSKEYIDGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_child_api_key_api_v1_access_api_keys__key_id__get',
    response_media_type='application/json',
)
async def get_child_api_key_api_v1_access_api_keys__key_id__get(transport: HttpTransport, request: GetChildApiKeyApiV1AccessApiKeysKeyIdGetRequest) -> GetChildApiKeyApiV1AccessApiKeysKeyIdGetSuccess:
    return await transport.invoke(GETCHILDAPIKEYAPIV1ACCESSAPIKEYSKEYIDGET_OPERATION, path_parameters={'key_id': str(request.key_id)}, query_parameters={}, body=None)

class ListDelegatedPassesApiV1AccessDelegatedPassesGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    pass

class ListDelegatedPassesApiV1AccessDelegatedPassesGetSuccess(RootModel[list[DelegatedPassPublic]]):
    pass

ListDelegatedPassesApiV1AccessDelegatedPassesGetError = SafeTransportError

LISTDELEGATEDPASSESAPIV1ACCESSDELEGATEDPASSESGET_SECURITY = SecurityMetadata(
    identity='access-session:list_delegated_passes_api_v1_access_delegated_passes_get', public=False, access_required=True,
    signed_request_required=False, human_intent_required=False,
    source_symbol='list_delegated_passes_api_v1_access_delegated_passes_get', review_owner='Stage 1B0-R7',
)
LISTDELEGATEDPASSESAPIV1ACCESSDELEGATEDPASSESGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0010', operation_id='list_delegated_passes_api_v1_access_delegated_passes_get',
    method='GET', path='/api/v1/access/delegated-passes', backend_tag='proof-of-access',
    product='Access', disposition='UI_REQUIRED',
    success_status=200, response_type=ListDelegatedPassesApiV1AccessDelegatedPassesGetSuccess, security=LISTDELEGATEDPASSESAPIV1ACCESSDELEGATEDPASSESGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:list_delegated_passes_api_v1_access_delegated_passes_get',
    response_media_type='application/json',
)
async def list_delegated_passes_api_v1_access_delegated_passes_get(transport: HttpTransport, request: ListDelegatedPassesApiV1AccessDelegatedPassesGetRequest) -> ListDelegatedPassesApiV1AccessDelegatedPassesGetSuccess:
    return await transport.invoke(LISTDELEGATEDPASSESAPIV1ACCESSDELEGATEDPASSESGET_OPERATION, path_parameters={}, query_parameters={}, body=None)

class GetDelegatedPassApiV1AccessDelegatedPassesDelegatedPassIdGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    delegated_pass_id: str

class GetDelegatedPassApiV1AccessDelegatedPassesDelegatedPassIdGetSuccess(RootModel[DelegatedPassPublic]):
    pass

GetDelegatedPassApiV1AccessDelegatedPassesDelegatedPassIdGetError = SafeTransportError

GETDELEGATEDPASSAPIV1ACCESSDELEGATEDPASSESDELEGATEDPASSIDGET_SECURITY = SecurityMetadata(
    identity='access-session:get_delegated_pass_api_v1_access_delegated_passes__delegated_pass_id__get', public=False, access_required=True,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_delegated_pass_api_v1_access_delegated_passes__delegated_pass_id__get', review_owner='Stage 1B0-R7',
)
GETDELEGATEDPASSAPIV1ACCESSDELEGATEDPASSESDELEGATEDPASSIDGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0013', operation_id='get_delegated_pass_api_v1_access_delegated_passes__delegated_pass_id__get',
    method='GET', path='/api/v1/access/delegated-passes/{delegated_pass_id}', backend_tag='proof-of-access',
    product='Access', disposition='UI_REQUIRED',
    success_status=200, response_type=GetDelegatedPassApiV1AccessDelegatedPassesDelegatedPassIdGetSuccess, security=GETDELEGATEDPASSAPIV1ACCESSDELEGATEDPASSESDELEGATEDPASSIDGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_delegated_pass_api_v1_access_delegated_passes__delegated_pass_id__get',
    response_media_type='application/json',
)
async def get_delegated_pass_api_v1_access_delegated_passes__delegated_pass_id__get(transport: HttpTransport, request: GetDelegatedPassApiV1AccessDelegatedPassesDelegatedPassIdGetRequest) -> GetDelegatedPassApiV1AccessDelegatedPassesDelegatedPassIdGetSuccess:
    return await transport.invoke(GETDELEGATEDPASSAPIV1ACCESSDELEGATEDPASSESDELEGATEDPASSIDGET_OPERATION, path_parameters={'delegated_pass_id': str(request.delegated_pass_id)}, query_parameters={}, body=None)

class GetHumanIntentApiV1AccessIntentsIntentIdGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    intent_id: str

class GetHumanIntentApiV1AccessIntentsIntentIdGetSuccess(RootModel[HumanIntentResponse]):
    pass

GetHumanIntentApiV1AccessIntentsIntentIdGetError = SafeTransportError

GETHUMANINTENTAPIV1ACCESSINTENTSINTENTIDGET_SECURITY = SecurityMetadata(
    identity='access-session:get_human_intent_api_v1_access_intents__intent_id__get', public=False, access_required=True,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_human_intent_api_v1_access_intents__intent_id__get', review_owner='Stage 1B0-R7',
)
GETHUMANINTENTAPIV1ACCESSINTENTSINTENTIDGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0016', operation_id='get_human_intent_api_v1_access_intents__intent_id__get',
    method='GET', path='/api/v1/access/intents/{intent_id}', backend_tag='proof-of-access',
    product='Access', disposition='UI_REQUIRED',
    success_status=200, response_type=GetHumanIntentApiV1AccessIntentsIntentIdGetSuccess, security=GETHUMANINTENTAPIV1ACCESSINTENTSINTENTIDGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_human_intent_api_v1_access_intents__intent_id__get',
    response_media_type='application/json',
)
async def get_human_intent_api_v1_access_intents__intent_id__get(transport: HttpTransport, request: GetHumanIntentApiV1AccessIntentsIntentIdGetRequest) -> GetHumanIntentApiV1AccessIntentsIntentIdGetSuccess:
    return await transport.invoke(GETHUMANINTENTAPIV1ACCESSINTENTSINTENTIDGET_OPERATION, path_parameters={'intent_id': str(request.intent_id)}, query_parameters={}, body=None)

class GetMeApiV1AccessMeGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    pass

class GetMeApiV1AccessMeGetSuccess(RootModel[AccessMeResponse]):
    pass

GetMeApiV1AccessMeGetError = SafeTransportError

GETMEAPIV1ACCESSMEGET_SECURITY = SecurityMetadata(
    identity='access-session:get_me_api_v1_access_me_get', public=False, access_required=True,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_me_api_v1_access_me_get', review_owner='Stage 1B0-R7',
)
GETMEAPIV1ACCESSMEGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0019', operation_id='get_me_api_v1_access_me_get',
    method='GET', path='/api/v1/access/me', backend_tag='proof-of-access',
    product='Access', disposition='UI_REQUIRED',
    success_status=200, response_type=GetMeApiV1AccessMeGetSuccess, security=GETMEAPIV1ACCESSMEGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_me_api_v1_access_me_get',
    response_media_type='application/json',
)
async def get_me_api_v1_access_me_get(transport: HttpTransport, request: GetMeApiV1AccessMeGetRequest) -> GetMeApiV1AccessMeGetSuccess:
    return await transport.invoke(GETMEAPIV1ACCESSMEGET_OPERATION, path_parameters={}, query_parameters={}, body=None)

class GetMyEntitlementsApiV1AccessMeEntitlementsGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    pass

class GetMyEntitlementsApiV1AccessMeEntitlementsGetSuccess(RootModel[SubscriptionEntitlementResponse]):
    pass

GetMyEntitlementsApiV1AccessMeEntitlementsGetError = SafeTransportError

GETMYENTITLEMENTSAPIV1ACCESSMEENTITLEMENTSGET_SECURITY = SecurityMetadata(
    identity='access-session:get_my_entitlements_api_v1_access_me_entitlements_get', public=False, access_required=True,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_my_entitlements_api_v1_access_me_entitlements_get', review_owner='Stage 1B0-R7',
)
GETMYENTITLEMENTSAPIV1ACCESSMEENTITLEMENTSGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0020', operation_id='get_my_entitlements_api_v1_access_me_entitlements_get',
    method='GET', path='/api/v1/access/me/entitlements', backend_tag='proof-of-access',
    product='Access', disposition='UI_REQUIRED',
    success_status=200, response_type=GetMyEntitlementsApiV1AccessMeEntitlementsGetSuccess, security=GETMYENTITLEMENTSAPIV1ACCESSMEENTITLEMENTSGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_my_entitlements_api_v1_access_me_entitlements_get',
    response_media_type='application/json',
)
async def get_my_entitlements_api_v1_access_me_entitlements_get(transport: HttpTransport, request: GetMyEntitlementsApiV1AccessMeEntitlementsGetRequest) -> GetMyEntitlementsApiV1AccessMeEntitlementsGetSuccess:
    return await transport.invoke(GETMYENTITLEMENTSAPIV1ACCESSMEENTITLEMENTSGET_OPERATION, path_parameters={}, query_parameters={}, body=None)

class GetMyLimitsApiV1AccessMeLimitsGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    pass

class GetMyLimitsApiV1AccessMeLimitsGetSuccess(RootModel[AccessLimitsResponse]):
    pass

GetMyLimitsApiV1AccessMeLimitsGetError = SafeTransportError

GETMYLIMITSAPIV1ACCESSMELIMITSGET_SECURITY = SecurityMetadata(
    identity='access-session:get_my_limits_api_v1_access_me_limits_get', public=False, access_required=True,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_my_limits_api_v1_access_me_limits_get', review_owner='Stage 1B0-R7',
)
GETMYLIMITSAPIV1ACCESSMELIMITSGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0021', operation_id='get_my_limits_api_v1_access_me_limits_get',
    method='GET', path='/api/v1/access/me/limits', backend_tag='proof-of-access',
    product='Access', disposition='UI_REQUIRED',
    success_status=200, response_type=GetMyLimitsApiV1AccessMeLimitsGetSuccess, security=GETMYLIMITSAPIV1ACCESSMELIMITSGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_my_limits_api_v1_access_me_limits_get',
    response_media_type='application/json',
)
async def get_my_limits_api_v1_access_me_limits_get(transport: HttpTransport, request: GetMyLimitsApiV1AccessMeLimitsGetRequest) -> GetMyLimitsApiV1AccessMeLimitsGetSuccess:
    return await transport.invoke(GETMYLIMITSAPIV1ACCESSMELIMITSGET_OPERATION, path_parameters={}, query_parameters={}, body=None)

class GetPaymentIntentStatusApiV1AccessPaymentIntentsPaymentIntentIdGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    payment_intent_id: int

class GetPaymentIntentStatusApiV1AccessPaymentIntentsPaymentIntentIdGetSuccess(RootModel[AccessPaymentIntentStatusResponse]):
    pass

GetPaymentIntentStatusApiV1AccessPaymentIntentsPaymentIntentIdGetError = SafeTransportError

GETPAYMENTINTENTSTATUSAPIV1ACCESSPAYMENTINTENTSPAYMENTINTENTIDGET_SECURITY = SecurityMetadata(
    identity='public:get_payment_intent_status_api_v1_access_payment_intents__payment_intent_id__get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_payment_intent_status_api_v1_access_payment_intents__payment_intent_id__get', review_owner='Stage 1B0-R7',
)
GETPAYMENTINTENTSTATUSAPIV1ACCESSPAYMENTINTENTSPAYMENTINTENTIDGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0023', operation_id='get_payment_intent_status_api_v1_access_payment_intents__payment_intent_id__get',
    method='GET', path='/api/v1/access/payment-intents/{payment_intent_id}', backend_tag='proof-of-access',
    product='Access', disposition='UI_REQUIRED',
    success_status=200, response_type=GetPaymentIntentStatusApiV1AccessPaymentIntentsPaymentIntentIdGetSuccess, security=GETPAYMENTINTENTSTATUSAPIV1ACCESSPAYMENTINTENTSPAYMENTINTENTIDGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_payment_intent_status_api_v1_access_payment_intents__payment_intent_id__get',
    response_media_type='application/json',
)
async def get_payment_intent_status_api_v1_access_payment_intents__payment_intent_id__get(transport: HttpTransport, request: GetPaymentIntentStatusApiV1AccessPaymentIntentsPaymentIntentIdGetRequest) -> GetPaymentIntentStatusApiV1AccessPaymentIntentsPaymentIntentIdGetSuccess:
    return await transport.invoke(GETPAYMENTINTENTSTATUSAPIV1ACCESSPAYMENTINTENTSPAYMENTINTENTIDGET_OPERATION, path_parameters={'payment_intent_id': str(request.payment_intent_id)}, query_parameters={}, body=None)

class RecoveryStatusApiV1AccessRecoveryStatusRecoveryAttemptIdGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    recovery_attempt_id: str

class RecoveryStatusApiV1AccessRecoveryStatusRecoveryAttemptIdGetSuccess(RootModel[RecoveryStatusResponse]):
    pass

RecoveryStatusApiV1AccessRecoveryStatusRecoveryAttemptIdGetError = SafeTransportError

RECOVERYSTATUSAPIV1ACCESSRECOVERYSTATUSRECOVERYATTEMPTIDGET_SECURITY = SecurityMetadata(
    identity='public:recovery_status_api_v1_access_recovery_status__recovery_attempt_id__get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='recovery_status_api_v1_access_recovery_status__recovery_attempt_id__get', review_owner='Stage 1B0-R7',
)
RECOVERYSTATUSAPIV1ACCESSRECOVERYSTATUSRECOVERYATTEMPTIDGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0031', operation_id='recovery_status_api_v1_access_recovery_status__recovery_attempt_id__get',
    method='GET', path='/api/v1/access/recovery/status/{recovery_attempt_id}', backend_tag='proof-of-access',
    product='Access', disposition='UI_REQUIRED',
    success_status=200, response_type=RecoveryStatusApiV1AccessRecoveryStatusRecoveryAttemptIdGetSuccess, security=RECOVERYSTATUSAPIV1ACCESSRECOVERYSTATUSRECOVERYATTEMPTIDGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:recovery_status_api_v1_access_recovery_status__recovery_attempt_id__get',
    response_media_type='application/json',
)
async def recovery_status_api_v1_access_recovery_status__recovery_attempt_id__get(transport: HttpTransport, request: RecoveryStatusApiV1AccessRecoveryStatusRecoveryAttemptIdGetRequest) -> RecoveryStatusApiV1AccessRecoveryStatusRecoveryAttemptIdGetSuccess:
    return await transport.invoke(RECOVERYSTATUSAPIV1ACCESSRECOVERYSTATUSRECOVERYATTEMPTIDGET_OPERATION, path_parameters={'recovery_attempt_id': str(request.recovery_attempt_id)}, query_parameters={}, body=None)

class ListAddressesApiV1BusinessLightningAddressesGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    pass

class ListAddressesApiV1BusinessLightningAddressesGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

ListAddressesApiV1BusinessLightningAddressesGetError = SafeTransportError

LISTADDRESSESAPIV1BUSINESSLIGHTNINGADDRESSESGET_SECURITY = SecurityMetadata(
    identity='public:list_addresses_api_v1_business_lightning_addresses_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='list_addresses_api_v1_business_lightning_addresses_get', review_owner='Stage 1B0-R7',
)
LISTADDRESSESAPIV1BUSINESSLIGHTNINGADDRESSESGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0041', operation_id='list_addresses_api_v1_business_lightning_addresses_get',
    method='GET', path='/api/v1/business/lightning-addresses', backend_tag='Merchant Lightning Address',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=ListAddressesApiV1BusinessLightningAddressesGetSuccess, security=LISTADDRESSESAPIV1BUSINESSLIGHTNINGADDRESSESGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:list_addresses_api_v1_business_lightning_addresses_get',
    response_media_type='application/json',
)
async def list_addresses_api_v1_business_lightning_addresses_get(transport: HttpTransport, request: ListAddressesApiV1BusinessLightningAddressesGetRequest) -> ListAddressesApiV1BusinessLightningAddressesGetSuccess:
    return await transport.invoke(LISTADDRESSESAPIV1BUSINESSLIGHTNINGADDRESSESGET_OPERATION, path_parameters={}, query_parameters={}, body=None)

class GetAddressApiV1BusinessLightningAddressesAddressIdGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    address_id: str

class GetAddressApiV1BusinessLightningAddressesAddressIdGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

GetAddressApiV1BusinessLightningAddressesAddressIdGetError = SafeTransportError

GETADDRESSAPIV1BUSINESSLIGHTNINGADDRESSESADDRESSIDGET_SECURITY = SecurityMetadata(
    identity='public:get_address_api_v1_business_lightning_addresses__address_id__get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_address_api_v1_business_lightning_addresses__address_id__get', review_owner='Stage 1B0-R7',
)
GETADDRESSAPIV1BUSINESSLIGHTNINGADDRESSESADDRESSIDGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0044', operation_id='get_address_api_v1_business_lightning_addresses__address_id__get',
    method='GET', path='/api/v1/business/lightning-addresses/{address_id}', backend_tag='Merchant Lightning Address',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetAddressApiV1BusinessLightningAddressesAddressIdGetSuccess, security=GETADDRESSAPIV1BUSINESSLIGHTNINGADDRESSESADDRESSIDGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_address_api_v1_business_lightning_addresses__address_id__get',
    response_media_type='application/json',
)
async def get_address_api_v1_business_lightning_addresses__address_id__get(transport: HttpTransport, request: GetAddressApiV1BusinessLightningAddressesAddressIdGetRequest) -> GetAddressApiV1BusinessLightningAddressesAddressIdGetSuccess:
    return await transport.invoke(GETADDRESSAPIV1BUSINESSLIGHTNINGADDRESSESADDRESSIDGET_OPERATION, path_parameters={'address_id': str(request.address_id)}, query_parameters={}, body=None)

class ListDomainsApiV1BusinessLightningDomainsGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    pass

class ListDomainsApiV1BusinessLightningDomainsGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

ListDomainsApiV1BusinessLightningDomainsGetError = SafeTransportError

LISTDOMAINSAPIV1BUSINESSLIGHTNINGDOMAINSGET_SECURITY = SecurityMetadata(
    identity='public:list_domains_api_v1_business_lightning_domains_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='list_domains_api_v1_business_lightning_domains_get', review_owner='Stage 1B0-R7',
)
LISTDOMAINSAPIV1BUSINESSLIGHTNINGDOMAINSGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0047', operation_id='list_domains_api_v1_business_lightning_domains_get',
    method='GET', path='/api/v1/business/lightning-domains', backend_tag='Merchant Lightning Address',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=ListDomainsApiV1BusinessLightningDomainsGetSuccess, security=LISTDOMAINSAPIV1BUSINESSLIGHTNINGDOMAINSGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:list_domains_api_v1_business_lightning_domains_get',
    response_media_type='application/json',
)
async def list_domains_api_v1_business_lightning_domains_get(transport: HttpTransport, request: ListDomainsApiV1BusinessLightningDomainsGetRequest) -> ListDomainsApiV1BusinessLightningDomainsGetSuccess:
    return await transport.invoke(LISTDOMAINSAPIV1BUSINESSLIGHTNINGDOMAINSGET_OPERATION, path_parameters={}, query_parameters={}, body=None)

class GetDomainApiV1BusinessLightningDomainsDomainIdGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    domain_id: str

class GetDomainApiV1BusinessLightningDomainsDomainIdGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

GetDomainApiV1BusinessLightningDomainsDomainIdGetError = SafeTransportError

GETDOMAINAPIV1BUSINESSLIGHTNINGDOMAINSDOMAINIDGET_SECURITY = SecurityMetadata(
    identity='public:get_domain_api_v1_business_lightning_domains__domain_id__get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_domain_api_v1_business_lightning_domains__domain_id__get', review_owner='Stage 1B0-R7',
)
GETDOMAINAPIV1BUSINESSLIGHTNINGDOMAINSDOMAINIDGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0050', operation_id='get_domain_api_v1_business_lightning_domains__domain_id__get',
    method='GET', path='/api/v1/business/lightning-domains/{domain_id}', backend_tag='Merchant Lightning Address',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetDomainApiV1BusinessLightningDomainsDomainIdGetSuccess, security=GETDOMAINAPIV1BUSINESSLIGHTNINGDOMAINSDOMAINIDGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_domain_api_v1_business_lightning_domains__domain_id__get',
    response_media_type='application/json',
)
async def get_domain_api_v1_business_lightning_domains__domain_id__get(transport: HttpTransport, request: GetDomainApiV1BusinessLightningDomainsDomainIdGetRequest) -> GetDomainApiV1BusinessLightningDomainsDomainIdGetSuccess:
    return await transport.invoke(GETDOMAINAPIV1BUSINESSLIGHTNINGDOMAINSDOMAINIDGET_OPERATION, path_parameters={'domain_id': str(request.domain_id)}, query_parameters={}, body=None)

class CitadelAssessmentApiV1CitadelAssessmentGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    owner_type: str | None = None
    owner_id: int | None = None
    force_refresh: bool | None = None
    max_age_hours: int | None = None

class CitadelAssessmentApiV1CitadelAssessmentGetSuccess(RootModel[ResponseEnvelopeCitadelAssessmentOut]):
    pass

CitadelAssessmentApiV1CitadelAssessmentGetError = SafeTransportError

CITADELASSESSMENTAPIV1CITADELASSESSMENTGET_SECURITY = SecurityMetadata(
    identity='public:citadel_assessment_api_v1_citadel_assessment_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='citadel_assessment_api_v1_citadel_assessment_get', review_owner='Stage 1B0-R7',
)
CITADELASSESSMENTAPIV1CITADELASSESSMENTGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0053', operation_id='citadel_assessment_api_v1_citadel_assessment_get',
    method='GET', path='/api/v1/citadel/assessment', backend_tag='citadel',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=CitadelAssessmentApiV1CitadelAssessmentGetSuccess, security=CITADELASSESSMENTAPIV1CITADELASSESSMENTGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:citadel_assessment_api_v1_citadel_assessment_get',
    response_media_type='application/json',
)
async def citadel_assessment_api_v1_citadel_assessment_get(transport: HttpTransport, request: CitadelAssessmentApiV1CitadelAssessmentGetRequest) -> CitadelAssessmentApiV1CitadelAssessmentGetSuccess:
    return await transport.invoke(CITADELASSESSMENTAPIV1CITADELASSESSMENTGET_OPERATION, path_parameters={}, query_parameters={'owner_type': serialize_query_value(request.owner_type), 'owner_id': serialize_query_value(request.owner_id), 'force_refresh': serialize_query_value(request.force_refresh), 'max_age_hours': serialize_query_value(request.max_age_hours)}, body=None)

class CitadelDependenciesApiV1CitadelDependenciesGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    owner_id: int | None = None

class CitadelDependenciesApiV1CitadelDependenciesGetSuccess(RootModel[ResponseEnvelopeCitadelDependencyGraphOut]):
    pass

CitadelDependenciesApiV1CitadelDependenciesGetError = SafeTransportError

CITADELDEPENDENCIESAPIV1CITADELDEPENDENCIESGET_SECURITY = SecurityMetadata(
    identity='public:citadel_dependencies_api_v1_citadel_dependencies_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='citadel_dependencies_api_v1_citadel_dependencies_get', review_owner='Stage 1B0-R7',
)
CITADELDEPENDENCIESAPIV1CITADELDEPENDENCIESGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0054', operation_id='citadel_dependencies_api_v1_citadel_dependencies_get',
    method='GET', path='/api/v1/citadel/dependencies', backend_tag='citadel',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=CitadelDependenciesApiV1CitadelDependenciesGetSuccess, security=CITADELDEPENDENCIESAPIV1CITADELDEPENDENCIESGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:citadel_dependencies_api_v1_citadel_dependencies_get',
    response_media_type='application/json',
)
async def citadel_dependencies_api_v1_citadel_dependencies_get(transport: HttpTransport, request: CitadelDependenciesApiV1CitadelDependenciesGetRequest) -> CitadelDependenciesApiV1CitadelDependenciesGetSuccess:
    return await transport.invoke(CITADELDEPENDENCIESAPIV1CITADELDEPENDENCIESGET_OPERATION, path_parameters={}, query_parameters={'owner_id': serialize_query_value(request.owner_id)}, body=None)

class CitadelInheritanceApiV1CitadelInheritanceGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    owner_id: int | None = None

class CitadelInheritanceApiV1CitadelInheritanceGetSuccess(RootModel[ResponseEnvelopeCitadelInheritanceOut]):
    pass

CitadelInheritanceApiV1CitadelInheritanceGetError = SafeTransportError

CITADELINHERITANCEAPIV1CITADELINHERITANCEGET_SECURITY = SecurityMetadata(
    identity='public:citadel_inheritance_api_v1_citadel_inheritance_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='citadel_inheritance_api_v1_citadel_inheritance_get', review_owner='Stage 1B0-R7',
)
CITADELINHERITANCEAPIV1CITADELINHERITANCEGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0055', operation_id='citadel_inheritance_api_v1_citadel_inheritance_get',
    method='GET', path='/api/v1/citadel/inheritance', backend_tag='citadel',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=CitadelInheritanceApiV1CitadelInheritanceGetSuccess, security=CITADELINHERITANCEAPIV1CITADELINHERITANCEGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:citadel_inheritance_api_v1_citadel_inheritance_get',
    response_media_type='application/json',
)
async def citadel_inheritance_api_v1_citadel_inheritance_get(transport: HttpTransport, request: CitadelInheritanceApiV1CitadelInheritanceGetRequest) -> CitadelInheritanceApiV1CitadelInheritanceGetSuccess:
    return await transport.invoke(CITADELINHERITANCEAPIV1CITADELINHERITANCEGET_OPERATION, path_parameters={}, query_parameters={'owner_id': serialize_query_value(request.owner_id)}, body=None)

class CitadelOverviewApiV1CitadelOverviewGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    owner_type: str | None = None
    owner_id: int | None = None
    force_refresh: bool | None = None
    max_age_hours: int | None = None

class CitadelOverviewApiV1CitadelOverviewGetSuccess(RootModel[ResponseEnvelopeCitadelOverviewOut]):
    pass

CitadelOverviewApiV1CitadelOverviewGetError = SafeTransportError

CITADELOVERVIEWAPIV1CITADELOVERVIEWGET_SECURITY = SecurityMetadata(
    identity='public:citadel_overview_api_v1_citadel_overview_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='citadel_overview_api_v1_citadel_overview_get', review_owner='Stage 1B0-R7',
)
CITADELOVERVIEWAPIV1CITADELOVERVIEWGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0056', operation_id='citadel_overview_api_v1_citadel_overview_get',
    method='GET', path='/api/v1/citadel/overview', backend_tag='citadel',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=CitadelOverviewApiV1CitadelOverviewGetSuccess, security=CITADELOVERVIEWAPIV1CITADELOVERVIEWGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:citadel_overview_api_v1_citadel_overview_get',
    response_media_type='application/json',
)
async def citadel_overview_api_v1_citadel_overview_get(transport: HttpTransport, request: CitadelOverviewApiV1CitadelOverviewGetRequest) -> CitadelOverviewApiV1CitadelOverviewGetSuccess:
    return await transport.invoke(CITADELOVERVIEWAPIV1CITADELOVERVIEWGET_OPERATION, path_parameters={}, query_parameters={'owner_type': serialize_query_value(request.owner_type), 'owner_id': serialize_query_value(request.owner_id), 'force_refresh': serialize_query_value(request.force_refresh), 'max_age_hours': serialize_query_value(request.max_age_hours)}, body=None)

class CitadelPolicyChecksApiV1CitadelPolicyChecksGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    owner_id: int | None = None

class CitadelPolicyChecksApiV1CitadelPolicyChecksGetSuccess(RootModel[ResponseEnvelopeCitadelPolicyChecksOut]):
    pass

CitadelPolicyChecksApiV1CitadelPolicyChecksGetError = SafeTransportError

CITADELPOLICYCHECKSAPIV1CITADELPOLICYCHECKSGET_SECURITY = SecurityMetadata(
    identity='public:citadel_policy_checks_api_v1_citadel_policy_checks_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='citadel_policy_checks_api_v1_citadel_policy_checks_get', review_owner='Stage 1B0-R7',
)
CITADELPOLICYCHECKSAPIV1CITADELPOLICYCHECKSGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0057', operation_id='citadel_policy_checks_api_v1_citadel_policy_checks_get',
    method='GET', path='/api/v1/citadel/policy-checks', backend_tag='citadel',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=CitadelPolicyChecksApiV1CitadelPolicyChecksGetSuccess, security=CITADELPOLICYCHECKSAPIV1CITADELPOLICYCHECKSGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:citadel_policy_checks_api_v1_citadel_policy_checks_get',
    response_media_type='application/json',
)
async def citadel_policy_checks_api_v1_citadel_policy_checks_get(transport: HttpTransport, request: CitadelPolicyChecksApiV1CitadelPolicyChecksGetRequest) -> CitadelPolicyChecksApiV1CitadelPolicyChecksGetSuccess:
    return await transport.invoke(CITADELPOLICYCHECKSAPIV1CITADELPOLICYCHECKSGET_OPERATION, path_parameters={}, query_parameters={'owner_id': serialize_query_value(request.owner_id)}, body=None)

class CitadelRecoveryApiV1CitadelRecoveryGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    owner_id: int | None = None

class CitadelRecoveryApiV1CitadelRecoveryGetSuccess(RootModel[ResponseEnvelopeRecoveryReadinessOut]):
    pass

CitadelRecoveryApiV1CitadelRecoveryGetError = SafeTransportError

CITADELRECOVERYAPIV1CITADELRECOVERYGET_SECURITY = SecurityMetadata(
    identity='public:citadel_recovery_api_v1_citadel_recovery_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='citadel_recovery_api_v1_citadel_recovery_get', review_owner='Stage 1B0-R7',
)
CITADELRECOVERYAPIV1CITADELRECOVERYGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0059', operation_id='citadel_recovery_api_v1_citadel_recovery_get',
    method='GET', path='/api/v1/citadel/recovery', backend_tag='citadel',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=CitadelRecoveryApiV1CitadelRecoveryGetSuccess, security=CITADELRECOVERYAPIV1CITADELRECOVERYGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:citadel_recovery_api_v1_citadel_recovery_get',
    response_media_type='application/json',
)
async def citadel_recovery_api_v1_citadel_recovery_get(transport: HttpTransport, request: CitadelRecoveryApiV1CitadelRecoveryGetRequest) -> CitadelRecoveryApiV1CitadelRecoveryGetSuccess:
    return await transport.invoke(CITADELRECOVERYAPIV1CITADELRECOVERYGET_OPERATION, path_parameters={}, query_parameters={'owner_id': serialize_query_value(request.owner_id)}, body=None)

class CitadelRepairPlanApiV1CitadelRepairPlanGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    owner_id: int | None = None

class CitadelRepairPlanApiV1CitadelRepairPlanGetSuccess(RootModel[ResponseEnvelopeCitadelRepairPlanOut]):
    pass

CitadelRepairPlanApiV1CitadelRepairPlanGetError = SafeTransportError

CITADELREPAIRPLANAPIV1CITADELREPAIRPLANGET_SECURITY = SecurityMetadata(
    identity='public:citadel_repair_plan_api_v1_citadel_repair_plan_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='citadel_repair_plan_api_v1_citadel_repair_plan_get', review_owner='Stage 1B0-R7',
)
CITADELREPAIRPLANAPIV1CITADELREPAIRPLANGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0060', operation_id='citadel_repair_plan_api_v1_citadel_repair_plan_get',
    method='GET', path='/api/v1/citadel/repair-plan', backend_tag='citadel',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=CitadelRepairPlanApiV1CitadelRepairPlanGetSuccess, security=CITADELREPAIRPLANAPIV1CITADELREPAIRPLANGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:citadel_repair_plan_api_v1_citadel_repair_plan_get',
    response_media_type='application/json',
)
async def citadel_repair_plan_api_v1_citadel_repair_plan_get(transport: HttpTransport, request: CitadelRepairPlanApiV1CitadelRepairPlanGetRequest) -> CitadelRepairPlanApiV1CitadelRepairPlanGetSuccess:
    return await transport.invoke(CITADELREPAIRPLANAPIV1CITADELREPAIRPLANGET_OPERATION, path_parameters={}, query_parameters={'owner_id': serialize_query_value(request.owner_id)}, body=None)

class ListSimulationsApiV1CitadelSimulationsGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    owner_id: int | None = None

class ListSimulationsApiV1CitadelSimulationsGetSuccess(RootModel[ResponseEnvelopeListCitadelSimulationOut]):
    pass

ListSimulationsApiV1CitadelSimulationsGetError = SafeTransportError

LISTSIMULATIONSAPIV1CITADELSIMULATIONSGET_SECURITY = SecurityMetadata(
    identity='public:list_simulations_api_v1_citadel_simulations_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='list_simulations_api_v1_citadel_simulations_get', review_owner='Stage 1B0-R7',
)
LISTSIMULATIONSAPIV1CITADELSIMULATIONSGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0061', operation_id='list_simulations_api_v1_citadel_simulations_get',
    method='GET', path='/api/v1/citadel/simulations', backend_tag='citadel',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=ListSimulationsApiV1CitadelSimulationsGetSuccess, security=LISTSIMULATIONSAPIV1CITADELSIMULATIONSGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:list_simulations_api_v1_citadel_simulations_get',
    response_media_type='application/json',
)
async def list_simulations_api_v1_citadel_simulations_get(transport: HttpTransport, request: ListSimulationsApiV1CitadelSimulationsGetRequest) -> ListSimulationsApiV1CitadelSimulationsGetSuccess:
    return await transport.invoke(LISTSIMULATIONSAPIV1CITADELSIMULATIONSGET_OPERATION, path_parameters={}, query_parameters={'owner_id': serialize_query_value(request.owner_id)}, body=None)

class ListSnippetsApiV1EducationSnippetsGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    pass

class ListSnippetsApiV1EducationSnippetsGetSuccess(RootModel[ResponseEnvelopeListEducationSnippetOut]):
    pass

ListSnippetsApiV1EducationSnippetsGetError = SafeTransportError

LISTSNIPPETSAPIV1EDUCATIONSNIPPETSGET_SECURITY = SecurityMetadata(
    identity='public:list_snippets_api_v1_education_snippets_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='list_snippets_api_v1_education_snippets_get', review_owner='Stage 1B0-R7',
)
LISTSNIPPETSAPIV1EDUCATIONSNIPPETSGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0063', operation_id='list_snippets_api_v1_education_snippets_get',
    method='GET', path='/api/v1/education/snippets', backend_tag='education',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=ListSnippetsApiV1EducationSnippetsGetSuccess, security=LISTSNIPPETSAPIV1EDUCATIONSNIPPETSGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:list_snippets_api_v1_education_snippets_get',
    response_media_type='application/json',
)
async def list_snippets_api_v1_education_snippets_get(transport: HttpTransport, request: ListSnippetsApiV1EducationSnippetsGetRequest) -> ListSnippetsApiV1EducationSnippetsGetSuccess:
    return await transport.invoke(LISTSNIPPETSAPIV1EDUCATIONSNIPPETSGET_OPERATION, path_parameters={}, query_parameters={}, body=None)

class ListEntitiesApiV1EntitiesGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    limit: int | None = None
    offset: int | None = None
    q: str | None | None = None
    entity_type: str | None | None = None
    min_confidence: Decimal | None | None = None

class ListEntitiesApiV1EntitiesGetSuccess(RootModel[ResponseEnvelopePaginatedDataEntityOut]):
    pass

ListEntitiesApiV1EntitiesGetError = SafeTransportError

LISTENTITIESAPIV1ENTITIESGET_SECURITY = SecurityMetadata(
    identity='public:list_entities_api_v1_entities_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='list_entities_api_v1_entities_get', review_owner='Stage 1B0-R7',
)
LISTENTITIESAPIV1ENTITIESGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0064', operation_id='list_entities_api_v1_entities_get',
    method='GET', path='/api/v1/entities', backend_tag='entities',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=ListEntitiesApiV1EntitiesGetSuccess, security=LISTENTITIESAPIV1ENTITIESGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:list_entities_api_v1_entities_get',
    response_media_type='application/json',
)
async def list_entities_api_v1_entities_get(transport: HttpTransport, request: ListEntitiesApiV1EntitiesGetRequest) -> ListEntitiesApiV1EntitiesGetSuccess:
    return await transport.invoke(LISTENTITIESAPIV1ENTITIESGET_OPERATION, path_parameters={}, query_parameters={'limit': serialize_query_value(request.limit), 'offset': serialize_query_value(request.offset), 'q': serialize_query_value(request.q), 'entity_type': serialize_query_value(request.entity_type), 'min_confidence': serialize_query_value(request.min_confidence)}, body=None)

class GetMarketMemoryEvidenceApiV1EvidenceMarketMemoryEventIdGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    event_id: int
    limit: int | None = None

class GetMarketMemoryEvidenceApiV1EvidenceMarketMemoryEventIdGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

GetMarketMemoryEvidenceApiV1EvidenceMarketMemoryEventIdGetError = SafeTransportError

GETMARKETMEMORYEVIDENCEAPIV1EVIDENCEMARKETMEMORYEVENTIDGET_SECURITY = SecurityMetadata(
    identity='public:get_market_memory_evidence_api_v1_evidence_market_memory__event_id__get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_market_memory_evidence_api_v1_evidence_market_memory__event_id__get', review_owner='Stage 1B0-R7',
)
GETMARKETMEMORYEVIDENCEAPIV1EVIDENCEMARKETMEMORYEVENTIDGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0067', operation_id='get_market_memory_evidence_api_v1_evidence_market_memory__event_id__get',
    method='GET', path='/api/v1/evidence/market-memory/{event_id}', backend_tag='evidence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetMarketMemoryEvidenceApiV1EvidenceMarketMemoryEventIdGetSuccess, security=GETMARKETMEMORYEVIDENCEAPIV1EVIDENCEMARKETMEMORYEVENTIDGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_market_memory_evidence_api_v1_evidence_market_memory__event_id__get',
    response_media_type='application/json',
)
async def get_market_memory_evidence_api_v1_evidence_market_memory__event_id__get(transport: HttpTransport, request: GetMarketMemoryEvidenceApiV1EvidenceMarketMemoryEventIdGetRequest) -> GetMarketMemoryEvidenceApiV1EvidenceMarketMemoryEventIdGetSuccess:
    return await transport.invoke(GETMARKETMEMORYEVIDENCEAPIV1EVIDENCEMARKETMEMORYEVENTIDGET_OPERATION, path_parameters={'event_id': str(request.event_id)}, query_parameters={'limit': serialize_query_value(request.limit)}, body=None)

class ListEvidencePacketsApiV1EvidencePacketsGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    limit: int | None = None

class ListEvidencePacketsApiV1EvidencePacketsGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

ListEvidencePacketsApiV1EvidencePacketsGetError = SafeTransportError

LISTEVIDENCEPACKETSAPIV1EVIDENCEPACKETSGET_SECURITY = SecurityMetadata(
    identity='public:list_evidence_packets_api_v1_evidence_packets_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='list_evidence_packets_api_v1_evidence_packets_get', review_owner='Stage 1B0-R7',
)
LISTEVIDENCEPACKETSAPIV1EVIDENCEPACKETSGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0068', operation_id='list_evidence_packets_api_v1_evidence_packets_get',
    method='GET', path='/api/v1/evidence/packets', backend_tag='evidence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=ListEvidencePacketsApiV1EvidencePacketsGetSuccess, security=LISTEVIDENCEPACKETSAPIV1EVIDENCEPACKETSGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:list_evidence_packets_api_v1_evidence_packets_get',
    response_media_type='application/json',
)
async def list_evidence_packets_api_v1_evidence_packets_get(transport: HttpTransport, request: ListEvidencePacketsApiV1EvidencePacketsGetRequest) -> ListEvidencePacketsApiV1EvidencePacketsGetSuccess:
    return await transport.invoke(LISTEVIDENCEPACKETSAPIV1EVIDENCEPACKETSGET_OPERATION, path_parameters={}, query_parameters={'limit': serialize_query_value(request.limit)}, body=None)

class GetEvidencePacketApiV1EvidencePacketsPacketIdGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    packet_id: int
    format: str | None = None

class GetEvidencePacketApiV1EvidencePacketsPacketIdGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

GetEvidencePacketApiV1EvidencePacketsPacketIdGetError = SafeTransportError

GETEVIDENCEPACKETAPIV1EVIDENCEPACKETSPACKETIDGET_SECURITY = SecurityMetadata(
    identity='public:get_evidence_packet_api_v1_evidence_packets__packet_id__get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_evidence_packet_api_v1_evidence_packets__packet_id__get', review_owner='Stage 1B0-R7',
)
GETEVIDENCEPACKETAPIV1EVIDENCEPACKETSPACKETIDGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0069', operation_id='get_evidence_packet_api_v1_evidence_packets__packet_id__get',
    method='GET', path='/api/v1/evidence/packets/{packet_id}', backend_tag='evidence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetEvidencePacketApiV1EvidencePacketsPacketIdGetSuccess, security=GETEVIDENCEPACKETAPIV1EVIDENCEPACKETSPACKETIDGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_evidence_packet_api_v1_evidence_packets__packet_id__get',
    response_media_type='application/json',
)
async def get_evidence_packet_api_v1_evidence_packets__packet_id__get(transport: HttpTransport, request: GetEvidencePacketApiV1EvidencePacketsPacketIdGetRequest) -> GetEvidencePacketApiV1EvidencePacketsPacketIdGetSuccess:
    return await transport.invoke(GETEVIDENCEPACKETAPIV1EVIDENCEPACKETSPACKETIDGET_OPERATION, path_parameters={'packet_id': str(request.packet_id)}, query_parameters={'format': serialize_query_value(request.format)}, body=None)

class GetEvidencePacketRelationshipsApiV1EvidencePacketsPacketIdRelationshipsGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    packet_id: int

class GetEvidencePacketRelationshipsApiV1EvidencePacketsPacketIdRelationshipsGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

GetEvidencePacketRelationshipsApiV1EvidencePacketsPacketIdRelationshipsGetError = SafeTransportError

GETEVIDENCEPACKETRELATIONSHIPSAPIV1EVIDENCEPACKETSPACKETIDRELATIONSHIPSGET_SECURITY = SecurityMetadata(
    identity='public:get_evidence_packet_relationships_api_v1_evidence_packets__packet_id__relationships_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_evidence_packet_relationships_api_v1_evidence_packets__packet_id__relationships_get', review_owner='Stage 1B0-R7',
)
GETEVIDENCEPACKETRELATIONSHIPSAPIV1EVIDENCEPACKETSPACKETIDRELATIONSHIPSGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0070', operation_id='get_evidence_packet_relationships_api_v1_evidence_packets__packet_id__relationships_get',
    method='GET', path='/api/v1/evidence/packets/{packet_id}/relationships', backend_tag='evidence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetEvidencePacketRelationshipsApiV1EvidencePacketsPacketIdRelationshipsGetSuccess, security=GETEVIDENCEPACKETRELATIONSHIPSAPIV1EVIDENCEPACKETSPACKETIDRELATIONSHIPSGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_evidence_packet_relationships_api_v1_evidence_packets__packet_id__relationships_get',
    response_media_type='application/json',
)
async def get_evidence_packet_relationships_api_v1_evidence_packets__packet_id__relationships_get(transport: HttpTransport, request: GetEvidencePacketRelationshipsApiV1EvidencePacketsPacketIdRelationshipsGetRequest) -> GetEvidencePacketRelationshipsApiV1EvidencePacketsPacketIdRelationshipsGetSuccess:
    return await transport.invoke(GETEVIDENCEPACKETRELATIONSHIPSAPIV1EVIDENCEPACKETSPACKETIDRELATIONSHIPSGET_OPERATION, path_parameters={'packet_id': str(request.packet_id)}, query_parameters={}, body=None)

class GetEvidencePacketTimelineApiV1EvidencePacketsPacketIdTimelineGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    packet_id: int

class GetEvidencePacketTimelineApiV1EvidencePacketsPacketIdTimelineGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

GetEvidencePacketTimelineApiV1EvidencePacketsPacketIdTimelineGetError = SafeTransportError

GETEVIDENCEPACKETTIMELINEAPIV1EVIDENCEPACKETSPACKETIDTIMELINEGET_SECURITY = SecurityMetadata(
    identity='public:get_evidence_packet_timeline_api_v1_evidence_packets__packet_id__timeline_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_evidence_packet_timeline_api_v1_evidence_packets__packet_id__timeline_get', review_owner='Stage 1B0-R7',
)
GETEVIDENCEPACKETTIMELINEAPIV1EVIDENCEPACKETSPACKETIDTIMELINEGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0071', operation_id='get_evidence_packet_timeline_api_v1_evidence_packets__packet_id__timeline_get',
    method='GET', path='/api/v1/evidence/packets/{packet_id}/timeline', backend_tag='evidence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetEvidencePacketTimelineApiV1EvidencePacketsPacketIdTimelineGetSuccess, security=GETEVIDENCEPACKETTIMELINEAPIV1EVIDENCEPACKETSPACKETIDTIMELINEGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_evidence_packet_timeline_api_v1_evidence_packets__packet_id__timeline_get',
    response_media_type='application/json',
)
async def get_evidence_packet_timeline_api_v1_evidence_packets__packet_id__timeline_get(transport: HttpTransport, request: GetEvidencePacketTimelineApiV1EvidencePacketsPacketIdTimelineGetRequest) -> GetEvidencePacketTimelineApiV1EvidencePacketsPacketIdTimelineGetSuccess:
    return await transport.invoke(GETEVIDENCEPACKETTIMELINEAPIV1EVIDENCEPACKETSPACKETIDTIMELINEGET_OPERATION, path_parameters={'packet_id': str(request.packet_id)}, query_parameters={}, body=None)

class ReplayEvidenceApiV1EvidenceReplayEntityTypeEntityIdGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    entity_type: str
    entity_id: int
    format: str | None = None

class ReplayEvidenceApiV1EvidenceReplayEntityTypeEntityIdGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

ReplayEvidenceApiV1EvidenceReplayEntityTypeEntityIdGetError = SafeTransportError

REPLAYEVIDENCEAPIV1EVIDENCEREPLAYENTITYTYPEENTITYIDGET_SECURITY = SecurityMetadata(
    identity='public:replay_evidence_api_v1_evidence_replay__entity_type___entity_id__get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='replay_evidence_api_v1_evidence_replay__entity_type___entity_id__get', review_owner='Stage 1B0-R7',
)
REPLAYEVIDENCEAPIV1EVIDENCEREPLAYENTITYTYPEENTITYIDGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0072', operation_id='replay_evidence_api_v1_evidence_replay__entity_type___entity_id__get',
    method='GET', path='/api/v1/evidence/replay/{entity_type}/{entity_id}', backend_tag='evidence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=ReplayEvidenceApiV1EvidenceReplayEntityTypeEntityIdGetSuccess, security=REPLAYEVIDENCEAPIV1EVIDENCEREPLAYENTITYTYPEENTITYIDGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:replay_evidence_api_v1_evidence_replay__entity_type___entity_id__get',
    response_media_type='application/json',
)
async def replay_evidence_api_v1_evidence_replay__entity_type___entity_id__get(transport: HttpTransport, request: ReplayEvidenceApiV1EvidenceReplayEntityTypeEntityIdGetRequest) -> ReplayEvidenceApiV1EvidenceReplayEntityTypeEntityIdGetSuccess:
    return await transport.invoke(REPLAYEVIDENCEAPIV1EVIDENCEREPLAYENTITYTYPEENTITYIDGET_OPERATION, path_parameters={'entity_type': str(request.entity_type), 'entity_id': str(request.entity_id)}, query_parameters={'format': serialize_query_value(request.format)}, body=None)

class ReplayEvidenceIntegrityApiV1EvidenceReplayEntityTypeEntityIdIntegrityGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    entity_type: str
    entity_id: int

class ReplayEvidenceIntegrityApiV1EvidenceReplayEntityTypeEntityIdIntegrityGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

ReplayEvidenceIntegrityApiV1EvidenceReplayEntityTypeEntityIdIntegrityGetError = SafeTransportError

REPLAYEVIDENCEINTEGRITYAPIV1EVIDENCEREPLAYENTITYTYPEENTITYIDINTEGRITYGET_SECURITY = SecurityMetadata(
    identity='public:replay_evidence_integrity_api_v1_evidence_replay__entity_type___entity_id__integrity_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='replay_evidence_integrity_api_v1_evidence_replay__entity_type___entity_id__integrity_get', review_owner='Stage 1B0-R7',
)
REPLAYEVIDENCEINTEGRITYAPIV1EVIDENCEREPLAYENTITYTYPEENTITYIDINTEGRITYGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0073', operation_id='replay_evidence_integrity_api_v1_evidence_replay__entity_type___entity_id__integrity_get',
    method='GET', path='/api/v1/evidence/replay/{entity_type}/{entity_id}/integrity', backend_tag='evidence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=ReplayEvidenceIntegrityApiV1EvidenceReplayEntityTypeEntityIdIntegrityGetSuccess, security=REPLAYEVIDENCEINTEGRITYAPIV1EVIDENCEREPLAYENTITYTYPEENTITYIDINTEGRITYGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:replay_evidence_integrity_api_v1_evidence_replay__entity_type___entity_id__integrity_get',
    response_media_type='application/json',
)
async def replay_evidence_integrity_api_v1_evidence_replay__entity_type___entity_id__integrity_get(transport: HttpTransport, request: ReplayEvidenceIntegrityApiV1EvidenceReplayEntityTypeEntityIdIntegrityGetRequest) -> ReplayEvidenceIntegrityApiV1EvidenceReplayEntityTypeEntityIdIntegrityGetSuccess:
    return await transport.invoke(REPLAYEVIDENCEINTEGRITYAPIV1EVIDENCEREPLAYENTITYTYPEENTITYIDINTEGRITYGET_OPERATION, path_parameters={'entity_type': str(request.entity_type), 'entity_id': str(request.entity_id)}, query_parameters={}, body=None)

class ReplayEvidenceTimelineApiV1EvidenceReplayEntityTypeEntityIdTimelineGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    entity_type: str
    entity_id: int

class ReplayEvidenceTimelineApiV1EvidenceReplayEntityTypeEntityIdTimelineGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

ReplayEvidenceTimelineApiV1EvidenceReplayEntityTypeEntityIdTimelineGetError = SafeTransportError

REPLAYEVIDENCETIMELINEAPIV1EVIDENCEREPLAYENTITYTYPEENTITYIDTIMELINEGET_SECURITY = SecurityMetadata(
    identity='public:replay_evidence_timeline_api_v1_evidence_replay__entity_type___entity_id__timeline_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='replay_evidence_timeline_api_v1_evidence_replay__entity_type___entity_id__timeline_get', review_owner='Stage 1B0-R7',
)
REPLAYEVIDENCETIMELINEAPIV1EVIDENCEREPLAYENTITYTYPEENTITYIDTIMELINEGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0074', operation_id='replay_evidence_timeline_api_v1_evidence_replay__entity_type___entity_id__timeline_get',
    method='GET', path='/api/v1/evidence/replay/{entity_type}/{entity_id}/timeline', backend_tag='evidence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=ReplayEvidenceTimelineApiV1EvidenceReplayEntityTypeEntityIdTimelineGetSuccess, security=REPLAYEVIDENCETIMELINEAPIV1EVIDENCEREPLAYENTITYTYPEENTITYIDTIMELINEGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:replay_evidence_timeline_api_v1_evidence_replay__entity_type___entity_id__timeline_get',
    response_media_type='application/json',
)
async def replay_evidence_timeline_api_v1_evidence_replay__entity_type___entity_id__timeline_get(transport: HttpTransport, request: ReplayEvidenceTimelineApiV1EvidenceReplayEntityTypeEntityIdTimelineGetRequest) -> ReplayEvidenceTimelineApiV1EvidenceReplayEntityTypeEntityIdTimelineGetSuccess:
    return await transport.invoke(REPLAYEVIDENCETIMELINEAPIV1EVIDENCEREPLAYENTITYTYPEENTITYIDTIMELINEGET_OPERATION, path_parameters={'entity_type': str(request.entity_type), 'entity_id': str(request.entity_id)}, query_parameters={}, body=None)

class HealthApiV1HealthGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    pass

class HealthApiV1HealthGetSuccess(RootModel[HealthOut]):
    pass

HealthApiV1HealthGetError = SafeTransportError

HEALTHAPIV1HEALTHGET_SECURITY = SecurityMetadata(
    identity='public:health_api_v1_health_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='health_api_v1_health_get', review_owner='Stage 1B0-R7',
)
HEALTHAPIV1HEALTHGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0076', operation_id='health_api_v1_health_get',
    method='GET', path='/api/v1/health', backend_tag='health',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=HealthApiV1HealthGetSuccess, security=HEALTHAPIV1HEALTHGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:health_api_v1_health_get',
    response_media_type='application/json',
)
async def health_api_v1_health_get(transport: HttpTransport, request: HealthApiV1HealthGetRequest) -> HealthApiV1HealthGetSuccess:
    return await transport.invoke(HEALTHAPIV1HEALTHGET_OPERATION, path_parameters={}, query_parameters={}, body=None)

class DegradedApiV1HealthDegradedGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    pass

class DegradedApiV1HealthDegradedGetSuccess(RootModel[list[DegradedComponentOut]]):
    pass

DegradedApiV1HealthDegradedGetError = SafeTransportError

DEGRADEDAPIV1HEALTHDEGRADEDGET_SECURITY = SecurityMetadata(
    identity='public:degraded_api_v1_health_degraded_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='degraded_api_v1_health_degraded_get', review_owner='Stage 1B0-R7',
)
DEGRADEDAPIV1HEALTHDEGRADEDGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0077', operation_id='degraded_api_v1_health_degraded_get',
    method='GET', path='/api/v1/health/degraded', backend_tag='health',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=DegradedApiV1HealthDegradedGetSuccess, security=DEGRADEDAPIV1HEALTHDEGRADEDGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:degraded_api_v1_health_degraded_get',
    response_media_type='application/json',
)
async def degraded_api_v1_health_degraded_get(transport: HttpTransport, request: DegradedApiV1HealthDegradedGetRequest) -> DegradedApiV1HealthDegradedGetSuccess:
    return await transport.invoke(DEGRADEDAPIV1HEALTHDEGRADEDGET_OPERATION, path_parameters={}, query_parameters={}, body=None)

class JobsApiV1HealthJobsGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    pass

class JobsApiV1HealthJobsGetSuccess(RootModel[list[BackgroundJobHealthOut]]):
    pass

JobsApiV1HealthJobsGetError = SafeTransportError

JOBSAPIV1HEALTHJOBSGET_SECURITY = SecurityMetadata(
    identity='public:jobs_api_v1_health_jobs_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='jobs_api_v1_health_jobs_get', review_owner='Stage 1B0-R7',
)
JOBSAPIV1HEALTHJOBSGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0078', operation_id='jobs_api_v1_health_jobs_get',
    method='GET', path='/api/v1/health/jobs', backend_tag='health',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=JobsApiV1HealthJobsGetSuccess, security=JOBSAPIV1HEALTHJOBSGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:jobs_api_v1_health_jobs_get',
    response_media_type='application/json',
)
async def jobs_api_v1_health_jobs_get(transport: HttpTransport, request: JobsApiV1HealthJobsGetRequest) -> JobsApiV1HealthJobsGetSuccess:
    return await transport.invoke(JOBSAPIV1HEALTHJOBSGET_OPERATION, path_parameters={}, query_parameters={}, body=None)

class LivenessApiV1HealthLiveGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    pass

class LivenessApiV1HealthLiveGetSuccess(RootModel[HealthOut]):
    pass

LivenessApiV1HealthLiveGetError = SafeTransportError

LIVENESSAPIV1HEALTHLIVEGET_SECURITY = SecurityMetadata(
    identity='public:liveness_api_v1_health_live_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='liveness_api_v1_health_live_get', review_owner='Stage 1B0-R7',
)
LIVENESSAPIV1HEALTHLIVEGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0079', operation_id='liveness_api_v1_health_live_get',
    method='GET', path='/api/v1/health/live', backend_tag='health',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=LivenessApiV1HealthLiveGetSuccess, security=LIVENESSAPIV1HEALTHLIVEGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:liveness_api_v1_health_live_get',
    response_media_type='application/json',
)
async def liveness_api_v1_health_live_get(transport: HttpTransport, request: LivenessApiV1HealthLiveGetRequest) -> LivenessApiV1HealthLiveGetSuccess:
    return await transport.invoke(LIVENESSAPIV1HEALTHLIVEGET_OPERATION, path_parameters={}, query_parameters={}, body=None)

class ProvidersApiV1HealthProvidersGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    pass

class ProvidersApiV1HealthProvidersGetSuccess(RootModel[list[ProviderHealthSnapshotOut]]):
    pass

ProvidersApiV1HealthProvidersGetError = SafeTransportError

PROVIDERSAPIV1HEALTHPROVIDERSGET_SECURITY = SecurityMetadata(
    identity='public:providers_api_v1_health_providers_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='providers_api_v1_health_providers_get', review_owner='Stage 1B0-R7',
)
PROVIDERSAPIV1HEALTHPROVIDERSGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0080', operation_id='providers_api_v1_health_providers_get',
    method='GET', path='/api/v1/health/providers', backend_tag='health',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=ProvidersApiV1HealthProvidersGetSuccess, security=PROVIDERSAPIV1HEALTHPROVIDERSGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:providers_api_v1_health_providers_get',
    response_media_type='application/json',
)
async def providers_api_v1_health_providers_get(transport: HttpTransport, request: ProvidersApiV1HealthProvidersGetRequest) -> ProvidersApiV1HealthProvidersGetSuccess:
    return await transport.invoke(PROVIDERSAPIV1HEALTHPROVIDERSGET_OPERATION, path_parameters={}, query_parameters={}, body=None)

class ReadinessApiV1HealthReadyGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    pass

class ReadinessApiV1HealthReadyGetSuccess(RootModel[HealthOut]):
    pass

ReadinessApiV1HealthReadyGetError = SafeTransportError

READINESSAPIV1HEALTHREADYGET_SECURITY = SecurityMetadata(
    identity='public:readiness_api_v1_health_ready_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='readiness_api_v1_health_ready_get', review_owner='Stage 1B0-R7',
)
READINESSAPIV1HEALTHREADYGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0081', operation_id='readiness_api_v1_health_ready_get',
    method='GET', path='/api/v1/health/ready', backend_tag='health',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=ReadinessApiV1HealthReadyGetSuccess, security=READINESSAPIV1HEALTHREADYGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:readiness_api_v1_health_ready_get',
    response_media_type='application/json',
)
async def readiness_api_v1_health_ready_get(transport: HttpTransport, request: ReadinessApiV1HealthReadyGetRequest) -> ReadinessApiV1HealthReadyGetSuccess:
    return await transport.invoke(READINESSAPIV1HEALTHREADYGET_OPERATION, path_parameters={}, query_parameters={}, body=None)

class RuntimeApiV1HealthRuntimeGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    pass

class RuntimeApiV1HealthRuntimeGetSuccess(RootModel[RuntimeStatusOut]):
    pass

RuntimeApiV1HealthRuntimeGetError = SafeTransportError

RUNTIMEAPIV1HEALTHRUNTIMEGET_SECURITY = SecurityMetadata(
    identity='public:runtime_api_v1_health_runtime_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='runtime_api_v1_health_runtime_get', review_owner='Stage 1B0-R7',
)
RUNTIMEAPIV1HEALTHRUNTIMEGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0082', operation_id='runtime_api_v1_health_runtime_get',
    method='GET', path='/api/v1/health/runtime', backend_tag='health',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=RuntimeApiV1HealthRuntimeGetSuccess, security=RUNTIMEAPIV1HEALTHRUNTIMEGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:runtime_api_v1_health_runtime_get',
    response_media_type='application/json',
)
async def runtime_api_v1_health_runtime_get(transport: HttpTransport, request: RuntimeApiV1HealthRuntimeGetRequest) -> RuntimeApiV1HealthRuntimeGetSuccess:
    return await transport.invoke(RUNTIMEAPIV1HEALTHRUNTIMEGET_OPERATION, path_parameters={}, query_parameters={}, body=None)

class SystemHealthApiV1HealthSystemGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    pass

class SystemHealthApiV1HealthSystemGetSuccess(RootModel[SystemHealthOut]):
    pass

SystemHealthApiV1HealthSystemGetError = SafeTransportError

SYSTEMHEALTHAPIV1HEALTHSYSTEMGET_SECURITY = SecurityMetadata(
    identity='public:system_health_api_v1_health_system_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='system_health_api_v1_health_system_get', review_owner='Stage 1B0-R7',
)
SYSTEMHEALTHAPIV1HEALTHSYSTEMGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0083', operation_id='system_health_api_v1_health_system_get',
    method='GET', path='/api/v1/health/system', backend_tag='health',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=SystemHealthApiV1HealthSystemGetSuccess, security=SYSTEMHEALTHAPIV1HEALTHSYSTEMGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:system_health_api_v1_health_system_get',
    response_media_type='application/json',
)
async def system_health_api_v1_health_system_get(transport: HttpTransport, request: SystemHealthApiV1HealthSystemGetRequest) -> SystemHealthApiV1HealthSystemGetSuccess:
    return await transport.invoke(SYSTEMHEALTHAPIV1HEALTHSYSTEMGET_OPERATION, path_parameters={}, query_parameters={}, body=None)

class GetCandleDashboardDtoApiV1IntelligenceCandlesCandleIdGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    candle_id: int

class GetCandleDashboardDtoApiV1IntelligenceCandlesCandleIdGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

GetCandleDashboardDtoApiV1IntelligenceCandlesCandleIdGetError = SafeTransportError

GETCANDLEDASHBOARDDTOAPIV1INTELLIGENCECANDLESCANDLEIDGET_SECURITY = SecurityMetadata(
    identity='public:get_candle_dashboard_dto_api_v1_intelligence_candles__candle_id__get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_candle_dashboard_dto_api_v1_intelligence_candles__candle_id__get', review_owner='Stage 1B0-R7',
)
GETCANDLEDASHBOARDDTOAPIV1INTELLIGENCECANDLESCANDLEIDGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0085', operation_id='get_candle_dashboard_dto_api_v1_intelligence_candles__candle_id__get',
    method='GET', path='/api/v1/intelligence/candles/{candle_id}', backend_tag='intelligence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetCandleDashboardDtoApiV1IntelligenceCandlesCandleIdGetSuccess, security=GETCANDLEDASHBOARDDTOAPIV1INTELLIGENCECANDLESCANDLEIDGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_candle_dashboard_dto_api_v1_intelligence_candles__candle_id__get',
    response_media_type='application/json',
)
async def get_candle_dashboard_dto_api_v1_intelligence_candles__candle_id__get(transport: HttpTransport, request: GetCandleDashboardDtoApiV1IntelligenceCandlesCandleIdGetRequest) -> GetCandleDashboardDtoApiV1IntelligenceCandlesCandleIdGetSuccess:
    return await transport.invoke(GETCANDLEDASHBOARDDTOAPIV1INTELLIGENCECANDLESCANDLEIDGET_OPERATION, path_parameters={'candle_id': str(request.candle_id)}, query_parameters={}, body=None)

class GetCandleAttributionApiV1IntelligenceCandlesCandleIdAttributionGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    candle_id: int
    limit: int | None = None

class GetCandleAttributionApiV1IntelligenceCandlesCandleIdAttributionGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

GetCandleAttributionApiV1IntelligenceCandlesCandleIdAttributionGetError = SafeTransportError

GETCANDLEATTRIBUTIONAPIV1INTELLIGENCECANDLESCANDLEIDATTRIBUTIONGET_SECURITY = SecurityMetadata(
    identity='public:get_candle_attribution_api_v1_intelligence_candles__candle_id__attribution_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_candle_attribution_api_v1_intelligence_candles__candle_id__attribution_get', review_owner='Stage 1B0-R7',
)
GETCANDLEATTRIBUTIONAPIV1INTELLIGENCECANDLESCANDLEIDATTRIBUTIONGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0086', operation_id='get_candle_attribution_api_v1_intelligence_candles__candle_id__attribution_get',
    method='GET', path='/api/v1/intelligence/candles/{candle_id}/attribution', backend_tag='intelligence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetCandleAttributionApiV1IntelligenceCandlesCandleIdAttributionGetSuccess, security=GETCANDLEATTRIBUTIONAPIV1INTELLIGENCECANDLESCANDLEIDATTRIBUTIONGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_candle_attribution_api_v1_intelligence_candles__candle_id__attribution_get',
    response_media_type='application/json',
)
async def get_candle_attribution_api_v1_intelligence_candles__candle_id__attribution_get(transport: HttpTransport, request: GetCandleAttributionApiV1IntelligenceCandlesCandleIdAttributionGetRequest) -> GetCandleAttributionApiV1IntelligenceCandlesCandleIdAttributionGetSuccess:
    return await transport.invoke(GETCANDLEATTRIBUTIONAPIV1INTELLIGENCECANDLESCANDLEIDATTRIBUTIONGET_OPERATION, path_parameters={'candle_id': str(request.candle_id)}, query_parameters={'limit': serialize_query_value(request.limit)}, body=None)

class GetCandleCandidatesApiV1IntelligenceCandlesCandleIdCandidatesGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    candle_id: int
    limit: int | None = None

class GetCandleCandidatesApiV1IntelligenceCandlesCandleIdCandidatesGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

GetCandleCandidatesApiV1IntelligenceCandlesCandleIdCandidatesGetError = SafeTransportError

GETCANDLECANDIDATESAPIV1INTELLIGENCECANDLESCANDLEIDCANDIDATESGET_SECURITY = SecurityMetadata(
    identity='public:get_candle_candidates_api_v1_intelligence_candles__candle_id__candidates_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_candle_candidates_api_v1_intelligence_candles__candle_id__candidates_get', review_owner='Stage 1B0-R7',
)
GETCANDLECANDIDATESAPIV1INTELLIGENCECANDLESCANDLEIDCANDIDATESGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0087', operation_id='get_candle_candidates_api_v1_intelligence_candles__candle_id__candidates_get',
    method='GET', path='/api/v1/intelligence/candles/{candle_id}/candidates', backend_tag='intelligence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetCandleCandidatesApiV1IntelligenceCandlesCandleIdCandidatesGetSuccess, security=GETCANDLECANDIDATESAPIV1INTELLIGENCECANDLESCANDLEIDCANDIDATESGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_candle_candidates_api_v1_intelligence_candles__candle_id__candidates_get',
    response_media_type='application/json',
)
async def get_candle_candidates_api_v1_intelligence_candles__candle_id__candidates_get(transport: HttpTransport, request: GetCandleCandidatesApiV1IntelligenceCandlesCandleIdCandidatesGetRequest) -> GetCandleCandidatesApiV1IntelligenceCandlesCandleIdCandidatesGetSuccess:
    return await transport.invoke(GETCANDLECANDIDATESAPIV1INTELLIGENCECANDLESCANDLEIDCANDIDATESGET_OPERATION, path_parameters={'candle_id': str(request.candle_id)}, query_parameters={'limit': serialize_query_value(request.limit)}, body=None)

class GetCandleContextApiV1IntelligenceCandlesCandleIdContextGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    candle_id: int

class GetCandleContextApiV1IntelligenceCandlesCandleIdContextGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

GetCandleContextApiV1IntelligenceCandlesCandleIdContextGetError = SafeTransportError

GETCANDLECONTEXTAPIV1INTELLIGENCECANDLESCANDLEIDCONTEXTGET_SECURITY = SecurityMetadata(
    identity='public:get_candle_context_api_v1_intelligence_candles__candle_id__context_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_candle_context_api_v1_intelligence_candles__candle_id__context_get', review_owner='Stage 1B0-R7',
)
GETCANDLECONTEXTAPIV1INTELLIGENCECANDLESCANDLEIDCONTEXTGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0088', operation_id='get_candle_context_api_v1_intelligence_candles__candle_id__context_get',
    method='GET', path='/api/v1/intelligence/candles/{candle_id}/context', backend_tag='intelligence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetCandleContextApiV1IntelligenceCandlesCandleIdContextGetSuccess, security=GETCANDLECONTEXTAPIV1INTELLIGENCECANDLESCANDLEIDCONTEXTGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_candle_context_api_v1_intelligence_candles__candle_id__context_get',
    response_media_type='application/json',
)
async def get_candle_context_api_v1_intelligence_candles__candle_id__context_get(transport: HttpTransport, request: GetCandleContextApiV1IntelligenceCandlesCandleIdContextGetRequest) -> GetCandleContextApiV1IntelligenceCandlesCandleIdContextGetSuccess:
    return await transport.invoke(GETCANDLECONTEXTAPIV1INTELLIGENCECANDLESCANDLEIDCONTEXTGET_OPERATION, path_parameters={'candle_id': str(request.candle_id)}, query_parameters={}, body=None)

class GetCandleEventsDashboardDtoApiV1IntelligenceCandlesCandleIdEventsGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    candle_id: int

class GetCandleEventsDashboardDtoApiV1IntelligenceCandlesCandleIdEventsGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

GetCandleEventsDashboardDtoApiV1IntelligenceCandlesCandleIdEventsGetError = SafeTransportError

GETCANDLEEVENTSDASHBOARDDTOAPIV1INTELLIGENCECANDLESCANDLEIDEVENTSGET_SECURITY = SecurityMetadata(
    identity='public:get_candle_events_dashboard_dto_api_v1_intelligence_candles__candle_id__events_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_candle_events_dashboard_dto_api_v1_intelligence_candles__candle_id__events_get', review_owner='Stage 1B0-R7',
)
GETCANDLEEVENTSDASHBOARDDTOAPIV1INTELLIGENCECANDLESCANDLEIDEVENTSGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0089', operation_id='get_candle_events_dashboard_dto_api_v1_intelligence_candles__candle_id__events_get',
    method='GET', path='/api/v1/intelligence/candles/{candle_id}/events', backend_tag='intelligence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetCandleEventsDashboardDtoApiV1IntelligenceCandlesCandleIdEventsGetSuccess, security=GETCANDLEEVENTSDASHBOARDDTOAPIV1INTELLIGENCECANDLESCANDLEIDEVENTSGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_candle_events_dashboard_dto_api_v1_intelligence_candles__candle_id__events_get',
    response_media_type='application/json',
)
async def get_candle_events_dashboard_dto_api_v1_intelligence_candles__candle_id__events_get(transport: HttpTransport, request: GetCandleEventsDashboardDtoApiV1IntelligenceCandlesCandleIdEventsGetRequest) -> GetCandleEventsDashboardDtoApiV1IntelligenceCandlesCandleIdEventsGetSuccess:
    return await transport.invoke(GETCANDLEEVENTSDASHBOARDDTOAPIV1INTELLIGENCECANDLESCANDLEIDEVENTSGET_OPERATION, path_parameters={'candle_id': str(request.candle_id)}, query_parameters={}, body=None)

class GetCandleEvidenceDashboardDtoApiV1IntelligenceCandlesCandleIdEvidenceGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    candle_id: int

class GetCandleEvidenceDashboardDtoApiV1IntelligenceCandlesCandleIdEvidenceGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

GetCandleEvidenceDashboardDtoApiV1IntelligenceCandlesCandleIdEvidenceGetError = SafeTransportError

GETCANDLEEVIDENCEDASHBOARDDTOAPIV1INTELLIGENCECANDLESCANDLEIDEVIDENCEGET_SECURITY = SecurityMetadata(
    identity='public:get_candle_evidence_dashboard_dto_api_v1_intelligence_candles__candle_id__evidence_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_candle_evidence_dashboard_dto_api_v1_intelligence_candles__candle_id__evidence_get', review_owner='Stage 1B0-R7',
)
GETCANDLEEVIDENCEDASHBOARDDTOAPIV1INTELLIGENCECANDLESCANDLEIDEVIDENCEGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0090', operation_id='get_candle_evidence_dashboard_dto_api_v1_intelligence_candles__candle_id__evidence_get',
    method='GET', path='/api/v1/intelligence/candles/{candle_id}/evidence', backend_tag='intelligence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetCandleEvidenceDashboardDtoApiV1IntelligenceCandlesCandleIdEvidenceGetSuccess, security=GETCANDLEEVIDENCEDASHBOARDDTOAPIV1INTELLIGENCECANDLESCANDLEIDEVIDENCEGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_candle_evidence_dashboard_dto_api_v1_intelligence_candles__candle_id__evidence_get',
    response_media_type='application/json',
)
async def get_candle_evidence_dashboard_dto_api_v1_intelligence_candles__candle_id__evidence_get(transport: HttpTransport, request: GetCandleEvidenceDashboardDtoApiV1IntelligenceCandlesCandleIdEvidenceGetRequest) -> GetCandleEvidenceDashboardDtoApiV1IntelligenceCandlesCandleIdEvidenceGetSuccess:
    return await transport.invoke(GETCANDLEEVIDENCEDASHBOARDDTOAPIV1INTELLIGENCECANDLESCANDLEIDEVIDENCEGET_OPERATION, path_parameters={'candle_id': str(request.candle_id)}, query_parameters={}, body=None)

class ExplainCandleApiV1IntelligenceCandlesCandleIdExplainGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    candle_id: int

class ExplainCandleApiV1IntelligenceCandlesCandleIdExplainGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

ExplainCandleApiV1IntelligenceCandlesCandleIdExplainGetError = SafeTransportError

EXPLAINCANDLEAPIV1INTELLIGENCECANDLESCANDLEIDEXPLAINGET_SECURITY = SecurityMetadata(
    identity='public:explain_candle_api_v1_intelligence_candles__candle_id__explain_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='explain_candle_api_v1_intelligence_candles__candle_id__explain_get', review_owner='Stage 1B0-R7',
)
EXPLAINCANDLEAPIV1INTELLIGENCECANDLESCANDLEIDEXPLAINGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0091', operation_id='explain_candle_api_v1_intelligence_candles__candle_id__explain_get',
    method='GET', path='/api/v1/intelligence/candles/{candle_id}/explain', backend_tag='intelligence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=ExplainCandleApiV1IntelligenceCandlesCandleIdExplainGetSuccess, security=EXPLAINCANDLEAPIV1INTELLIGENCECANDLESCANDLEIDEXPLAINGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:explain_candle_api_v1_intelligence_candles__candle_id__explain_get',
    response_media_type='application/json',
)
async def explain_candle_api_v1_intelligence_candles__candle_id__explain_get(transport: HttpTransport, request: ExplainCandleApiV1IntelligenceCandlesCandleIdExplainGetRequest) -> ExplainCandleApiV1IntelligenceCandlesCandleIdExplainGetSuccess:
    return await transport.invoke(EXPLAINCANDLEAPIV1INTELLIGENCECANDLESCANDLEIDEXPLAINGET_OPERATION, path_parameters={'candle_id': str(request.candle_id)}, query_parameters={}, body=None)

class GetCandleReplayApiV1IntelligenceCandlesCandleIdReplayGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    candle_id: int
    limit: int | None = None

class GetCandleReplayApiV1IntelligenceCandlesCandleIdReplayGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

GetCandleReplayApiV1IntelligenceCandlesCandleIdReplayGetError = SafeTransportError

GETCANDLEREPLAYAPIV1INTELLIGENCECANDLESCANDLEIDREPLAYGET_SECURITY = SecurityMetadata(
    identity='public:get_candle_replay_api_v1_intelligence_candles__candle_id__replay_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_candle_replay_api_v1_intelligence_candles__candle_id__replay_get', review_owner='Stage 1B0-R7',
)
GETCANDLEREPLAYAPIV1INTELLIGENCECANDLESCANDLEIDREPLAYGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0092', operation_id='get_candle_replay_api_v1_intelligence_candles__candle_id__replay_get',
    method='GET', path='/api/v1/intelligence/candles/{candle_id}/replay', backend_tag='intelligence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetCandleReplayApiV1IntelligenceCandlesCandleIdReplayGetSuccess, security=GETCANDLEREPLAYAPIV1INTELLIGENCECANDLESCANDLEIDREPLAYGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_candle_replay_api_v1_intelligence_candles__candle_id__replay_get',
    response_media_type='application/json',
)
async def get_candle_replay_api_v1_intelligence_candles__candle_id__replay_get(transport: HttpTransport, request: GetCandleReplayApiV1IntelligenceCandlesCandleIdReplayGetRequest) -> GetCandleReplayApiV1IntelligenceCandlesCandleIdReplayGetSuccess:
    return await transport.invoke(GETCANDLEREPLAYAPIV1INTELLIGENCECANDLESCANDLEIDREPLAYGET_OPERATION, path_parameters={'candle_id': str(request.candle_id)}, query_parameters={'limit': serialize_query_value(request.limit)}, body=None)

class GetCandleSimilarityDashboardDtoApiV1IntelligenceCandlesCandleIdSimilarGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    candle_id: int
    limit: int | None = None

class GetCandleSimilarityDashboardDtoApiV1IntelligenceCandlesCandleIdSimilarGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

GetCandleSimilarityDashboardDtoApiV1IntelligenceCandlesCandleIdSimilarGetError = SafeTransportError

GETCANDLESIMILARITYDASHBOARDDTOAPIV1INTELLIGENCECANDLESCANDLEIDSIMILARGET_SECURITY = SecurityMetadata(
    identity='public:get_candle_similarity_dashboard_dto_api_v1_intelligence_candles__candle_id__similar_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_candle_similarity_dashboard_dto_api_v1_intelligence_candles__candle_id__similar_get', review_owner='Stage 1B0-R7',
)
GETCANDLESIMILARITYDASHBOARDDTOAPIV1INTELLIGENCECANDLESCANDLEIDSIMILARGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0093', operation_id='get_candle_similarity_dashboard_dto_api_v1_intelligence_candles__candle_id__similar_get',
    method='GET', path='/api/v1/intelligence/candles/{candle_id}/similar', backend_tag='intelligence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetCandleSimilarityDashboardDtoApiV1IntelligenceCandlesCandleIdSimilarGetSuccess, security=GETCANDLESIMILARITYDASHBOARDDTOAPIV1INTELLIGENCECANDLESCANDLEIDSIMILARGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_candle_similarity_dashboard_dto_api_v1_intelligence_candles__candle_id__similar_get',
    response_media_type='application/json',
)
async def get_candle_similarity_dashboard_dto_api_v1_intelligence_candles__candle_id__similar_get(transport: HttpTransport, request: GetCandleSimilarityDashboardDtoApiV1IntelligenceCandlesCandleIdSimilarGetRequest) -> GetCandleSimilarityDashboardDtoApiV1IntelligenceCandlesCandleIdSimilarGetSuccess:
    return await transport.invoke(GETCANDLESIMILARITYDASHBOARDDTOAPIV1INTELLIGENCECANDLESCANDLEIDSIMILARGET_OPERATION, path_parameters={'candle_id': str(request.candle_id)}, query_parameters={'limit': serialize_query_value(request.limit)}, body=None)

class GetCandleTopEventsApiV1IntelligenceCandlesCandleIdTopEventsGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    candle_id: int
    limit: int | None = None

class GetCandleTopEventsApiV1IntelligenceCandlesCandleIdTopEventsGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

GetCandleTopEventsApiV1IntelligenceCandlesCandleIdTopEventsGetError = SafeTransportError

GETCANDLETOPEVENTSAPIV1INTELLIGENCECANDLESCANDLEIDTOPEVENTSGET_SECURITY = SecurityMetadata(
    identity='public:get_candle_top_events_api_v1_intelligence_candles__candle_id__top_events_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_candle_top_events_api_v1_intelligence_candles__candle_id__top_events_get', review_owner='Stage 1B0-R7',
)
GETCANDLETOPEVENTSAPIV1INTELLIGENCECANDLESCANDLEIDTOPEVENTSGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0094', operation_id='get_candle_top_events_api_v1_intelligence_candles__candle_id__top_events_get',
    method='GET', path='/api/v1/intelligence/candles/{candle_id}/top-events', backend_tag='intelligence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetCandleTopEventsApiV1IntelligenceCandlesCandleIdTopEventsGetSuccess, security=GETCANDLETOPEVENTSAPIV1INTELLIGENCECANDLESCANDLEIDTOPEVENTSGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_candle_top_events_api_v1_intelligence_candles__candle_id__top_events_get',
    response_media_type='application/json',
)
async def get_candle_top_events_api_v1_intelligence_candles__candle_id__top_events_get(transport: HttpTransport, request: GetCandleTopEventsApiV1IntelligenceCandlesCandleIdTopEventsGetRequest) -> GetCandleTopEventsApiV1IntelligenceCandlesCandleIdTopEventsGetSuccess:
    return await transport.invoke(GETCANDLETOPEVENTSAPIV1INTELLIGENCECANDLESCANDLEIDTOPEVENTSGET_OPERATION, path_parameters={'candle_id': str(request.candle_id)}, query_parameters={'limit': serialize_query_value(request.limit)}, body=None)

class GetEventMarketMemoryApiV1IntelligenceEventsEventIdMemoryGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    event_id: int

class GetEventMarketMemoryApiV1IntelligenceEventsEventIdMemoryGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

GetEventMarketMemoryApiV1IntelligenceEventsEventIdMemoryGetError = SafeTransportError

GETEVENTMARKETMEMORYAPIV1INTELLIGENCEEVENTSEVENTIDMEMORYGET_SECURITY = SecurityMetadata(
    identity='public:get_event_market_memory_api_v1_intelligence_events__event_id__memory_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_event_market_memory_api_v1_intelligence_events__event_id__memory_get', review_owner='Stage 1B0-R7',
)
GETEVENTMARKETMEMORYAPIV1INTELLIGENCEEVENTSEVENTIDMEMORYGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0095', operation_id='get_event_market_memory_api_v1_intelligence_events__event_id__memory_get',
    method='GET', path='/api/v1/intelligence/events/{event_id}/memory', backend_tag='intelligence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetEventMarketMemoryApiV1IntelligenceEventsEventIdMemoryGetSuccess, security=GETEVENTMARKETMEMORYAPIV1INTELLIGENCEEVENTSEVENTIDMEMORYGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_event_market_memory_api_v1_intelligence_events__event_id__memory_get',
    response_media_type='application/json',
)
async def get_event_market_memory_api_v1_intelligence_events__event_id__memory_get(transport: HttpTransport, request: GetEventMarketMemoryApiV1IntelligenceEventsEventIdMemoryGetRequest) -> GetEventMarketMemoryApiV1IntelligenceEventsEventIdMemoryGetSuccess:
    return await transport.invoke(GETEVENTMARKETMEMORYAPIV1INTELLIGENCEEVENTSEVENTIDMEMORYGET_OPERATION, path_parameters={'event_id': str(request.event_id)}, query_parameters={}, body=None)

class GetEventMarketMemoryReplayApiV1IntelligenceEventsEventIdMemoryReplayGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    event_id: int
    limit: int | None = None

class GetEventMarketMemoryReplayApiV1IntelligenceEventsEventIdMemoryReplayGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

GetEventMarketMemoryReplayApiV1IntelligenceEventsEventIdMemoryReplayGetError = SafeTransportError

GETEVENTMARKETMEMORYREPLAYAPIV1INTELLIGENCEEVENTSEVENTIDMEMORYREPLAYGET_SECURITY = SecurityMetadata(
    identity='public:get_event_market_memory_replay_api_v1_intelligence_events__event_id__memory_replay_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_event_market_memory_replay_api_v1_intelligence_events__event_id__memory_replay_get', review_owner='Stage 1B0-R7',
)
GETEVENTMARKETMEMORYREPLAYAPIV1INTELLIGENCEEVENTSEVENTIDMEMORYREPLAYGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0097', operation_id='get_event_market_memory_replay_api_v1_intelligence_events__event_id__memory_replay_get',
    method='GET', path='/api/v1/intelligence/events/{event_id}/memory/replay', backend_tag='intelligence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetEventMarketMemoryReplayApiV1IntelligenceEventsEventIdMemoryReplayGetSuccess, security=GETEVENTMARKETMEMORYREPLAYAPIV1INTELLIGENCEEVENTSEVENTIDMEMORYREPLAYGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_event_market_memory_replay_api_v1_intelligence_events__event_id__memory_replay_get',
    response_media_type='application/json',
)
async def get_event_market_memory_replay_api_v1_intelligence_events__event_id__memory_replay_get(transport: HttpTransport, request: GetEventMarketMemoryReplayApiV1IntelligenceEventsEventIdMemoryReplayGetRequest) -> GetEventMarketMemoryReplayApiV1IntelligenceEventsEventIdMemoryReplayGetSuccess:
    return await transport.invoke(GETEVENTMARKETMEMORYREPLAYAPIV1INTELLIGENCEEVENTSEVENTIDMEMORYREPLAYGET_OPERATION, path_parameters={'event_id': str(request.event_id)}, query_parameters={'limit': serialize_query_value(request.limit)}, body=None)

class GetEventMarketMemorySimilarityApiV1IntelligenceEventsEventIdSimilarGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    event_id: int
    limit: int | None = None

class GetEventMarketMemorySimilarityApiV1IntelligenceEventsEventIdSimilarGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

GetEventMarketMemorySimilarityApiV1IntelligenceEventsEventIdSimilarGetError = SafeTransportError

GETEVENTMARKETMEMORYSIMILARITYAPIV1INTELLIGENCEEVENTSEVENTIDSIMILARGET_SECURITY = SecurityMetadata(
    identity='public:get_event_market_memory_similarity_api_v1_intelligence_events__event_id__similar_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_event_market_memory_similarity_api_v1_intelligence_events__event_id__similar_get', review_owner='Stage 1B0-R7',
)
GETEVENTMARKETMEMORYSIMILARITYAPIV1INTELLIGENCEEVENTSEVENTIDSIMILARGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0098', operation_id='get_event_market_memory_similarity_api_v1_intelligence_events__event_id__similar_get',
    method='GET', path='/api/v1/intelligence/events/{event_id}/similar', backend_tag='intelligence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetEventMarketMemorySimilarityApiV1IntelligenceEventsEventIdSimilarGetSuccess, security=GETEVENTMARKETMEMORYSIMILARITYAPIV1INTELLIGENCEEVENTSEVENTIDSIMILARGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_event_market_memory_similarity_api_v1_intelligence_events__event_id__similar_get',
    response_media_type='application/json',
)
async def get_event_market_memory_similarity_api_v1_intelligence_events__event_id__similar_get(transport: HttpTransport, request: GetEventMarketMemorySimilarityApiV1IntelligenceEventsEventIdSimilarGetRequest) -> GetEventMarketMemorySimilarityApiV1IntelligenceEventsEventIdSimilarGetSuccess:
    return await transport.invoke(GETEVENTMARKETMEMORYSIMILARITYAPIV1INTELLIGENCEEVENTSEVENTIDSIMILARGET_OPERATION, path_parameters={'event_id': str(request.event_id)}, query_parameters={'limit': serialize_query_value(request.limit)}, body=None)

class GetEventTimelineDashboardDtoApiV1IntelligenceEventsEventIdTimelineGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    event_id: int

class GetEventTimelineDashboardDtoApiV1IntelligenceEventsEventIdTimelineGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

GetEventTimelineDashboardDtoApiV1IntelligenceEventsEventIdTimelineGetError = SafeTransportError

GETEVENTTIMELINEDASHBOARDDTOAPIV1INTELLIGENCEEVENTSEVENTIDTIMELINEGET_SECURITY = SecurityMetadata(
    identity='public:get_event_timeline_dashboard_dto_api_v1_intelligence_events__event_id__timeline_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_event_timeline_dashboard_dto_api_v1_intelligence_events__event_id__timeline_get', review_owner='Stage 1B0-R7',
)
GETEVENTTIMELINEDASHBOARDDTOAPIV1INTELLIGENCEEVENTSEVENTIDTIMELINEGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0099', operation_id='get_event_timeline_dashboard_dto_api_v1_intelligence_events__event_id__timeline_get',
    method='GET', path='/api/v1/intelligence/events/{event_id}/timeline', backend_tag='intelligence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetEventTimelineDashboardDtoApiV1IntelligenceEventsEventIdTimelineGetSuccess, security=GETEVENTTIMELINEDASHBOARDDTOAPIV1INTELLIGENCEEVENTSEVENTIDTIMELINEGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_event_timeline_dashboard_dto_api_v1_intelligence_events__event_id__timeline_get',
    response_media_type='application/json',
)
async def get_event_timeline_dashboard_dto_api_v1_intelligence_events__event_id__timeline_get(transport: HttpTransport, request: GetEventTimelineDashboardDtoApiV1IntelligenceEventsEventIdTimelineGetRequest) -> GetEventTimelineDashboardDtoApiV1IntelligenceEventsEventIdTimelineGetSuccess:
    return await transport.invoke(GETEVENTTIMELINEDASHBOARDDTOAPIV1INTELLIGENCEEVENTSEVENTIDTIMELINEGET_OPERATION, path_parameters={'event_id': str(request.event_id)}, query_parameters={}, body=None)

class GetHighConfidenceImpactsApiV1IntelligenceImpactHighConfidenceGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    limit: int | None = None

class GetHighConfidenceImpactsApiV1IntelligenceImpactHighConfidenceGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

GetHighConfidenceImpactsApiV1IntelligenceImpactHighConfidenceGetError = SafeTransportError

GETHIGHCONFIDENCEIMPACTSAPIV1INTELLIGENCEIMPACTHIGHCONFIDENCEGET_SECURITY = SecurityMetadata(
    identity='public:get_high_confidence_impacts_api_v1_intelligence_impact_high_confidence_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_high_confidence_impacts_api_v1_intelligence_impact_high_confidence_get', review_owner='Stage 1B0-R7',
)
GETHIGHCONFIDENCEIMPACTSAPIV1INTELLIGENCEIMPACTHIGHCONFIDENCEGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0100', operation_id='get_high_confidence_impacts_api_v1_intelligence_impact_high_confidence_get',
    method='GET', path='/api/v1/intelligence/impact/high-confidence', backend_tag='intelligence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetHighConfidenceImpactsApiV1IntelligenceImpactHighConfidenceGetSuccess, security=GETHIGHCONFIDENCEIMPACTSAPIV1INTELLIGENCEIMPACTHIGHCONFIDENCEGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_high_confidence_impacts_api_v1_intelligence_impact_high_confidence_get',
    response_media_type='application/json',
)
async def get_high_confidence_impacts_api_v1_intelligence_impact_high_confidence_get(transport: HttpTransport, request: GetHighConfidenceImpactsApiV1IntelligenceImpactHighConfidenceGetRequest) -> GetHighConfidenceImpactsApiV1IntelligenceImpactHighConfidenceGetSuccess:
    return await transport.invoke(GETHIGHCONFIDENCEIMPACTSAPIV1INTELLIGENCEIMPACTHIGHCONFIDENCEGET_OPERATION, path_parameters={}, query_parameters={'limit': serialize_query_value(request.limit)}, body=None)

class ListNarrativesApiV1IntelligenceNarrativesGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    pass

class ListNarrativesApiV1IntelligenceNarrativesGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

ListNarrativesApiV1IntelligenceNarrativesGetError = SafeTransportError

LISTNARRATIVESAPIV1INTELLIGENCENARRATIVESGET_SECURITY = SecurityMetadata(
    identity='public:list_narratives_api_v1_intelligence_narratives_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='list_narratives_api_v1_intelligence_narratives_get', review_owner='Stage 1B0-R7',
)
LISTNARRATIVESAPIV1INTELLIGENCENARRATIVESGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0101', operation_id='list_narratives_api_v1_intelligence_narratives_get',
    method='GET', path='/api/v1/intelligence/narratives', backend_tag='intelligence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=ListNarrativesApiV1IntelligenceNarrativesGetSuccess, security=LISTNARRATIVESAPIV1INTELLIGENCENARRATIVESGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:list_narratives_api_v1_intelligence_narratives_get',
    response_media_type='application/json',
)
async def list_narratives_api_v1_intelligence_narratives_get(transport: HttpTransport, request: ListNarrativesApiV1IntelligenceNarrativesGetRequest) -> ListNarrativesApiV1IntelligenceNarrativesGetSuccess:
    return await transport.invoke(LISTNARRATIVESAPIV1INTELLIGENCENARRATIVESGET_OPERATION, path_parameters={}, query_parameters={}, body=None)

class GetActiveNarrativeMemoryApiV1IntelligenceNarrativesActiveGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    pass

class GetActiveNarrativeMemoryApiV1IntelligenceNarrativesActiveGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

GetActiveNarrativeMemoryApiV1IntelligenceNarrativesActiveGetError = SafeTransportError

GETACTIVENARRATIVEMEMORYAPIV1INTELLIGENCENARRATIVESACTIVEGET_SECURITY = SecurityMetadata(
    identity='public:get_active_narrative_memory_api_v1_intelligence_narratives_active_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_active_narrative_memory_api_v1_intelligence_narratives_active_get', review_owner='Stage 1B0-R7',
)
GETACTIVENARRATIVEMEMORYAPIV1INTELLIGENCENARRATIVESACTIVEGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0102', operation_id='get_active_narrative_memory_api_v1_intelligence_narratives_active_get',
    method='GET', path='/api/v1/intelligence/narratives/active', backend_tag='intelligence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetActiveNarrativeMemoryApiV1IntelligenceNarrativesActiveGetSuccess, security=GETACTIVENARRATIVEMEMORYAPIV1INTELLIGENCENARRATIVESACTIVEGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_active_narrative_memory_api_v1_intelligence_narratives_active_get',
    response_media_type='application/json',
)
async def get_active_narrative_memory_api_v1_intelligence_narratives_active_get(transport: HttpTransport, request: GetActiveNarrativeMemoryApiV1IntelligenceNarrativesActiveGetRequest) -> GetActiveNarrativeMemoryApiV1IntelligenceNarrativesActiveGetSuccess:
    return await transport.invoke(GETACTIVENARRATIVEMEMORYAPIV1INTELLIGENCENARRATIVESACTIVEGET_OPERATION, path_parameters={}, query_parameters={}, body=None)

class GetNarrativeDominanceApiV1IntelligenceNarrativesDominanceGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    pass

class GetNarrativeDominanceApiV1IntelligenceNarrativesDominanceGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

GetNarrativeDominanceApiV1IntelligenceNarrativesDominanceGetError = SafeTransportError

GETNARRATIVEDOMINANCEAPIV1INTELLIGENCENARRATIVESDOMINANCEGET_SECURITY = SecurityMetadata(
    identity='public:get_narrative_dominance_api_v1_intelligence_narratives_dominance_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_narrative_dominance_api_v1_intelligence_narratives_dominance_get', review_owner='Stage 1B0-R7',
)
GETNARRATIVEDOMINANCEAPIV1INTELLIGENCENARRATIVESDOMINANCEGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0103', operation_id='get_narrative_dominance_api_v1_intelligence_narratives_dominance_get',
    method='GET', path='/api/v1/intelligence/narratives/dominance', backend_tag='intelligence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetNarrativeDominanceApiV1IntelligenceNarrativesDominanceGetSuccess, security=GETNARRATIVEDOMINANCEAPIV1INTELLIGENCENARRATIVESDOMINANCEGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_narrative_dominance_api_v1_intelligence_narratives_dominance_get',
    response_media_type='application/json',
)
async def get_narrative_dominance_api_v1_intelligence_narratives_dominance_get(transport: HttpTransport, request: GetNarrativeDominanceApiV1IntelligenceNarrativesDominanceGetRequest) -> GetNarrativeDominanceApiV1IntelligenceNarrativesDominanceGetSuccess:
    return await transport.invoke(GETNARRATIVEDOMINANCEAPIV1INTELLIGENCENARRATIVESDOMINANCEGET_OPERATION, path_parameters={}, query_parameters={}, body=None)

class GetDominantNarrativesApiV1IntelligenceNarrativesDominantGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    pass

class GetDominantNarrativesApiV1IntelligenceNarrativesDominantGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

GetDominantNarrativesApiV1IntelligenceNarrativesDominantGetError = SafeTransportError

GETDOMINANTNARRATIVESAPIV1INTELLIGENCENARRATIVESDOMINANTGET_SECURITY = SecurityMetadata(
    identity='public:get_dominant_narratives_api_v1_intelligence_narratives_dominant_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_dominant_narratives_api_v1_intelligence_narratives_dominant_get', review_owner='Stage 1B0-R7',
)
GETDOMINANTNARRATIVESAPIV1INTELLIGENCENARRATIVESDOMINANTGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0104', operation_id='get_dominant_narratives_api_v1_intelligence_narratives_dominant_get',
    method='GET', path='/api/v1/intelligence/narratives/dominant', backend_tag='intelligence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetDominantNarrativesApiV1IntelligenceNarrativesDominantGetSuccess, security=GETDOMINANTNARRATIVESAPIV1INTELLIGENCENARRATIVESDOMINANTGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_dominant_narratives_api_v1_intelligence_narratives_dominant_get',
    response_media_type='application/json',
)
async def get_dominant_narratives_api_v1_intelligence_narratives_dominant_get(transport: HttpTransport, request: GetDominantNarrativesApiV1IntelligenceNarrativesDominantGetRequest) -> GetDominantNarrativesApiV1IntelligenceNarrativesDominantGetSuccess:
    return await transport.invoke(GETDOMINANTNARRATIVESAPIV1INTELLIGENCENARRATIVESDOMINANTGET_OPERATION, path_parameters={}, query_parameters={}, body=None)

class GetEmergingNarrativesApiV1IntelligenceNarrativesEmergingGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    pass

class GetEmergingNarrativesApiV1IntelligenceNarrativesEmergingGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

GetEmergingNarrativesApiV1IntelligenceNarrativesEmergingGetError = SafeTransportError

GETEMERGINGNARRATIVESAPIV1INTELLIGENCENARRATIVESEMERGINGGET_SECURITY = SecurityMetadata(
    identity='public:get_emerging_narratives_api_v1_intelligence_narratives_emerging_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_emerging_narratives_api_v1_intelligence_narratives_emerging_get', review_owner='Stage 1B0-R7',
)
GETEMERGINGNARRATIVESAPIV1INTELLIGENCENARRATIVESEMERGINGGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0105', operation_id='get_emerging_narratives_api_v1_intelligence_narratives_emerging_get',
    method='GET', path='/api/v1/intelligence/narratives/emerging', backend_tag='intelligence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetEmergingNarrativesApiV1IntelligenceNarrativesEmergingGetSuccess, security=GETEMERGINGNARRATIVESAPIV1INTELLIGENCENARRATIVESEMERGINGGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_emerging_narratives_api_v1_intelligence_narratives_emerging_get',
    response_media_type='application/json',
)
async def get_emerging_narratives_api_v1_intelligence_narratives_emerging_get(transport: HttpTransport, request: GetEmergingNarrativesApiV1IntelligenceNarrativesEmergingGetRequest) -> GetEmergingNarrativesApiV1IntelligenceNarrativesEmergingGetSuccess:
    return await transport.invoke(GETEMERGINGNARRATIVESAPIV1INTELLIGENCENARRATIVESEMERGINGGET_OPERATION, path_parameters={}, query_parameters={}, body=None)

class GetFallingNarrativesApiV1IntelligenceNarrativesFallingGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    pass

class GetFallingNarrativesApiV1IntelligenceNarrativesFallingGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

GetFallingNarrativesApiV1IntelligenceNarrativesFallingGetError = SafeTransportError

GETFALLINGNARRATIVESAPIV1INTELLIGENCENARRATIVESFALLINGGET_SECURITY = SecurityMetadata(
    identity='public:get_falling_narratives_api_v1_intelligence_narratives_falling_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_falling_narratives_api_v1_intelligence_narratives_falling_get', review_owner='Stage 1B0-R7',
)
GETFALLINGNARRATIVESAPIV1INTELLIGENCENARRATIVESFALLINGGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0106', operation_id='get_falling_narratives_api_v1_intelligence_narratives_falling_get',
    method='GET', path='/api/v1/intelligence/narratives/falling', backend_tag='intelligence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetFallingNarrativesApiV1IntelligenceNarrativesFallingGetSuccess, security=GETFALLINGNARRATIVESAPIV1INTELLIGENCENARRATIVESFALLINGGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_falling_narratives_api_v1_intelligence_narratives_falling_get',
    response_media_type='application/json',
)
async def get_falling_narratives_api_v1_intelligence_narratives_falling_get(transport: HttpTransport, request: GetFallingNarrativesApiV1IntelligenceNarrativesFallingGetRequest) -> GetFallingNarrativesApiV1IntelligenceNarrativesFallingGetSuccess:
    return await transport.invoke(GETFALLINGNARRATIVESAPIV1INTELLIGENCENARRATIVESFALLINGGET_OPERATION, path_parameters={}, query_parameters={}, body=None)

class GetNarrativeHeatmapApiV1IntelligenceNarrativesHeatmapGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    window: str | None = None

class GetNarrativeHeatmapApiV1IntelligenceNarrativesHeatmapGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

GetNarrativeHeatmapApiV1IntelligenceNarrativesHeatmapGetError = SafeTransportError

GETNARRATIVEHEATMAPAPIV1INTELLIGENCENARRATIVESHEATMAPGET_SECURITY = SecurityMetadata(
    identity='public:get_narrative_heatmap_api_v1_intelligence_narratives_heatmap_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_narrative_heatmap_api_v1_intelligence_narratives_heatmap_get', review_owner='Stage 1B0-R7',
)
GETNARRATIVEHEATMAPAPIV1INTELLIGENCENARRATIVESHEATMAPGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0107', operation_id='get_narrative_heatmap_api_v1_intelligence_narratives_heatmap_get',
    method='GET', path='/api/v1/intelligence/narratives/heatmap', backend_tag='intelligence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetNarrativeHeatmapApiV1IntelligenceNarrativesHeatmapGetSuccess, security=GETNARRATIVEHEATMAPAPIV1INTELLIGENCENARRATIVESHEATMAPGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_narrative_heatmap_api_v1_intelligence_narratives_heatmap_get',
    response_media_type='application/json',
)
async def get_narrative_heatmap_api_v1_intelligence_narratives_heatmap_get(transport: HttpTransport, request: GetNarrativeHeatmapApiV1IntelligenceNarrativesHeatmapGetRequest) -> GetNarrativeHeatmapApiV1IntelligenceNarrativesHeatmapGetSuccess:
    return await transport.invoke(GETNARRATIVEHEATMAPAPIV1INTELLIGENCENARRATIVESHEATMAPGET_OPERATION, path_parameters={}, query_parameters={'window': serialize_query_value(request.window)}, body=None)

class GetNarrativeHistoryApiV1IntelligenceNarrativesHistoryGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    period: str | None = None
    limit: int | None = None

class GetNarrativeHistoryApiV1IntelligenceNarrativesHistoryGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

GetNarrativeHistoryApiV1IntelligenceNarrativesHistoryGetError = SafeTransportError

GETNARRATIVEHISTORYAPIV1INTELLIGENCENARRATIVESHISTORYGET_SECURITY = SecurityMetadata(
    identity='public:get_narrative_history_api_v1_intelligence_narratives_history_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_narrative_history_api_v1_intelligence_narratives_history_get', review_owner='Stage 1B0-R7',
)
GETNARRATIVEHISTORYAPIV1INTELLIGENCENARRATIVESHISTORYGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0108', operation_id='get_narrative_history_api_v1_intelligence_narratives_history_get',
    method='GET', path='/api/v1/intelligence/narratives/history', backend_tag='intelligence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetNarrativeHistoryApiV1IntelligenceNarrativesHistoryGetSuccess, security=GETNARRATIVEHISTORYAPIV1INTELLIGENCENARRATIVESHISTORYGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_narrative_history_api_v1_intelligence_narratives_history_get',
    response_media_type='application/json',
)
async def get_narrative_history_api_v1_intelligence_narratives_history_get(transport: HttpTransport, request: GetNarrativeHistoryApiV1IntelligenceNarrativesHistoryGetRequest) -> GetNarrativeHistoryApiV1IntelligenceNarrativesHistoryGetSuccess:
    return await transport.invoke(GETNARRATIVEHISTORYAPIV1INTELLIGENCENARRATIVESHISTORYGET_OPERATION, path_parameters={}, query_parameters={'period': serialize_query_value(request.period), 'limit': serialize_query_value(request.limit)}, body=None)

class GetNarrativeMemoryApiV1IntelligenceNarrativesMemoryGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    pass

class GetNarrativeMemoryApiV1IntelligenceNarrativesMemoryGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

GetNarrativeMemoryApiV1IntelligenceNarrativesMemoryGetError = SafeTransportError

GETNARRATIVEMEMORYAPIV1INTELLIGENCENARRATIVESMEMORYGET_SECURITY = SecurityMetadata(
    identity='public:get_narrative_memory_api_v1_intelligence_narratives_memory_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_narrative_memory_api_v1_intelligence_narratives_memory_get', review_owner='Stage 1B0-R7',
)
GETNARRATIVEMEMORYAPIV1INTELLIGENCENARRATIVESMEMORYGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0109', operation_id='get_narrative_memory_api_v1_intelligence_narratives_memory_get',
    method='GET', path='/api/v1/intelligence/narratives/memory', backend_tag='intelligence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetNarrativeMemoryApiV1IntelligenceNarrativesMemoryGetSuccess, security=GETNARRATIVEMEMORYAPIV1INTELLIGENCENARRATIVESMEMORYGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_narrative_memory_api_v1_intelligence_narratives_memory_get',
    response_media_type='application/json',
)
async def get_narrative_memory_api_v1_intelligence_narratives_memory_get(transport: HttpTransport, request: GetNarrativeMemoryApiV1IntelligenceNarrativesMemoryGetRequest) -> GetNarrativeMemoryApiV1IntelligenceNarrativesMemoryGetSuccess:
    return await transport.invoke(GETNARRATIVEMEMORYAPIV1INTELLIGENCENARRATIVESMEMORYGET_OPERATION, path_parameters={}, query_parameters={}, body=None)

class GetRisingNarrativesApiV1IntelligenceNarrativesRisingGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    pass

class GetRisingNarrativesApiV1IntelligenceNarrativesRisingGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

GetRisingNarrativesApiV1IntelligenceNarrativesRisingGetError = SafeTransportError

GETRISINGNARRATIVESAPIV1INTELLIGENCENARRATIVESRISINGGET_SECURITY = SecurityMetadata(
    identity='public:get_rising_narratives_api_v1_intelligence_narratives_rising_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_rising_narratives_api_v1_intelligence_narratives_rising_get', review_owner='Stage 1B0-R7',
)
GETRISINGNARRATIVESAPIV1INTELLIGENCENARRATIVESRISINGGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0110', operation_id='get_rising_narratives_api_v1_intelligence_narratives_rising_get',
    method='GET', path='/api/v1/intelligence/narratives/rising', backend_tag='intelligence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetRisingNarrativesApiV1IntelligenceNarrativesRisingGetSuccess, security=GETRISINGNARRATIVESAPIV1INTELLIGENCENARRATIVESRISINGGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_rising_narratives_api_v1_intelligence_narratives_rising_get',
    response_media_type='application/json',
)
async def get_rising_narratives_api_v1_intelligence_narratives_rising_get(transport: HttpTransport, request: GetRisingNarrativesApiV1IntelligenceNarrativesRisingGetRequest) -> GetRisingNarrativesApiV1IntelligenceNarrativesRisingGetSuccess:
    return await transport.invoke(GETRISINGNARRATIVESAPIV1INTELLIGENCENARRATIVESRISINGGET_OPERATION, path_parameters={}, query_parameters={}, body=None)

class GetNarrativeRotationsApiV1IntelligenceNarrativesRotationsGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    pass

class GetNarrativeRotationsApiV1IntelligenceNarrativesRotationsGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

GetNarrativeRotationsApiV1IntelligenceNarrativesRotationsGetError = SafeTransportError

GETNARRATIVEROTATIONSAPIV1INTELLIGENCENARRATIVESROTATIONSGET_SECURITY = SecurityMetadata(
    identity='public:get_narrative_rotations_api_v1_intelligence_narratives_rotations_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_narrative_rotations_api_v1_intelligence_narratives_rotations_get', review_owner='Stage 1B0-R7',
)
GETNARRATIVEROTATIONSAPIV1INTELLIGENCENARRATIVESROTATIONSGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0111', operation_id='get_narrative_rotations_api_v1_intelligence_narratives_rotations_get',
    method='GET', path='/api/v1/intelligence/narratives/rotations', backend_tag='intelligence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetNarrativeRotationsApiV1IntelligenceNarrativesRotationsGetSuccess, security=GETNARRATIVEROTATIONSAPIV1INTELLIGENCENARRATIVESROTATIONSGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_narrative_rotations_api_v1_intelligence_narratives_rotations_get',
    response_media_type='application/json',
)
async def get_narrative_rotations_api_v1_intelligence_narratives_rotations_get(transport: HttpTransport, request: GetNarrativeRotationsApiV1IntelligenceNarrativesRotationsGetRequest) -> GetNarrativeRotationsApiV1IntelligenceNarrativesRotationsGetSuccess:
    return await transport.invoke(GETNARRATIVEROTATIONSAPIV1INTELLIGENCENARRATIVESROTATIONSGET_OPERATION, path_parameters={}, query_parameters={}, body=None)

class GetTopNarrativesApiV1IntelligenceNarrativesTopGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    pass

class GetTopNarrativesApiV1IntelligenceNarrativesTopGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

GetTopNarrativesApiV1IntelligenceNarrativesTopGetError = SafeTransportError

GETTOPNARRATIVESAPIV1INTELLIGENCENARRATIVESTOPGET_SECURITY = SecurityMetadata(
    identity='public:get_top_narratives_api_v1_intelligence_narratives_top_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_top_narratives_api_v1_intelligence_narratives_top_get', review_owner='Stage 1B0-R7',
)
GETTOPNARRATIVESAPIV1INTELLIGENCENARRATIVESTOPGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0112', operation_id='get_top_narratives_api_v1_intelligence_narratives_top_get',
    method='GET', path='/api/v1/intelligence/narratives/top', backend_tag='intelligence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetTopNarrativesApiV1IntelligenceNarrativesTopGetSuccess, security=GETTOPNARRATIVESAPIV1INTELLIGENCENARRATIVESTOPGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_top_narratives_api_v1_intelligence_narratives_top_get',
    response_media_type='application/json',
)
async def get_top_narratives_api_v1_intelligence_narratives_top_get(transport: HttpTransport, request: GetTopNarrativesApiV1IntelligenceNarrativesTopGetRequest) -> GetTopNarrativesApiV1IntelligenceNarrativesTopGetSuccess:
    return await transport.invoke(GETTOPNARRATIVESAPIV1INTELLIGENCENARRATIVESTOPGET_OPERATION, path_parameters={}, query_parameters={}, body=None)

class GetNarrativeApiV1IntelligenceNarrativesSlugGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    slug: str

class GetNarrativeApiV1IntelligenceNarrativesSlugGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

GetNarrativeApiV1IntelligenceNarrativesSlugGetError = SafeTransportError

GETNARRATIVEAPIV1INTELLIGENCENARRATIVESSLUGGET_SECURITY = SecurityMetadata(
    identity='public:get_narrative_api_v1_intelligence_narratives__slug__get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_narrative_api_v1_intelligence_narratives__slug__get', review_owner='Stage 1B0-R7',
)
GETNARRATIVEAPIV1INTELLIGENCENARRATIVESSLUGGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0113', operation_id='get_narrative_api_v1_intelligence_narratives__slug__get',
    method='GET', path='/api/v1/intelligence/narratives/{slug}', backend_tag='intelligence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetNarrativeApiV1IntelligenceNarrativesSlugGetSuccess, security=GETNARRATIVEAPIV1INTELLIGENCENARRATIVESSLUGGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_narrative_api_v1_intelligence_narratives__slug__get',
    response_media_type='application/json',
)
async def get_narrative_api_v1_intelligence_narratives__slug__get(transport: HttpTransport, request: GetNarrativeApiV1IntelligenceNarrativesSlugGetRequest) -> GetNarrativeApiV1IntelligenceNarrativesSlugGetSuccess:
    return await transport.invoke(GETNARRATIVEAPIV1INTELLIGENCENARRATIVESSLUGGET_OPERATION, path_parameters={'slug': str(request.slug)}, query_parameters={}, body=None)

class ListMarketPatternsApiV1IntelligencePatternsGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    pass

class ListMarketPatternsApiV1IntelligencePatternsGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

ListMarketPatternsApiV1IntelligencePatternsGetError = SafeTransportError

LISTMARKETPATTERNSAPIV1INTELLIGENCEPATTERNSGET_SECURITY = SecurityMetadata(
    identity='public:list_market_patterns_api_v1_intelligence_patterns_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='list_market_patterns_api_v1_intelligence_patterns_get', review_owner='Stage 1B0-R7',
)
LISTMARKETPATTERNSAPIV1INTELLIGENCEPATTERNSGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0114', operation_id='list_market_patterns_api_v1_intelligence_patterns_get',
    method='GET', path='/api/v1/intelligence/patterns', backend_tag='intelligence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=ListMarketPatternsApiV1IntelligencePatternsGetSuccess, security=LISTMARKETPATTERNSAPIV1INTELLIGENCEPATTERNSGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:list_market_patterns_api_v1_intelligence_patterns_get',
    response_media_type='application/json',
)
async def list_market_patterns_api_v1_intelligence_patterns_get(transport: HttpTransport, request: ListMarketPatternsApiV1IntelligencePatternsGetRequest) -> ListMarketPatternsApiV1IntelligencePatternsGetSuccess:
    return await transport.invoke(LISTMARKETPATTERNSAPIV1INTELLIGENCEPATTERNSGET_OPERATION, path_parameters={}, query_parameters={}, body=None)

class GetMarketPatternApiV1IntelligencePatternsPatternIdGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    pattern_id: str

class GetMarketPatternApiV1IntelligencePatternsPatternIdGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

GetMarketPatternApiV1IntelligencePatternsPatternIdGetError = SafeTransportError

GETMARKETPATTERNAPIV1INTELLIGENCEPATTERNSPATTERNIDGET_SECURITY = SecurityMetadata(
    identity='public:get_market_pattern_api_v1_intelligence_patterns__pattern_id__get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_market_pattern_api_v1_intelligence_patterns__pattern_id__get', review_owner='Stage 1B0-R7',
)
GETMARKETPATTERNAPIV1INTELLIGENCEPATTERNSPATTERNIDGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0115', operation_id='get_market_pattern_api_v1_intelligence_patterns__pattern_id__get',
    method='GET', path='/api/v1/intelligence/patterns/{pattern_id}', backend_tag='intelligence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetMarketPatternApiV1IntelligencePatternsPatternIdGetSuccess, security=GETMARKETPATTERNAPIV1INTELLIGENCEPATTERNSPATTERNIDGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_market_pattern_api_v1_intelligence_patterns__pattern_id__get',
    response_media_type='application/json',
)
async def get_market_pattern_api_v1_intelligence_patterns__pattern_id__get(transport: HttpTransport, request: GetMarketPatternApiV1IntelligencePatternsPatternIdGetRequest) -> GetMarketPatternApiV1IntelligencePatternsPatternIdGetSuccess:
    return await transport.invoke(GETMARKETPATTERNAPIV1INTELLIGENCEPATTERNSPATTERNIDGET_OPERATION, path_parameters={'pattern_id': str(request.pattern_id)}, query_parameters={}, body=None)

class GetMarketPatternHistoryApiV1IntelligencePatternsPatternIdHistoryGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    pattern_id: str

class GetMarketPatternHistoryApiV1IntelligencePatternsPatternIdHistoryGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

GetMarketPatternHistoryApiV1IntelligencePatternsPatternIdHistoryGetError = SafeTransportError

GETMARKETPATTERNHISTORYAPIV1INTELLIGENCEPATTERNSPATTERNIDHISTORYGET_SECURITY = SecurityMetadata(
    identity='public:get_market_pattern_history_api_v1_intelligence_patterns__pattern_id__history_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_market_pattern_history_api_v1_intelligence_patterns__pattern_id__history_get', review_owner='Stage 1B0-R7',
)
GETMARKETPATTERNHISTORYAPIV1INTELLIGENCEPATTERNSPATTERNIDHISTORYGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0116', operation_id='get_market_pattern_history_api_v1_intelligence_patterns__pattern_id__history_get',
    method='GET', path='/api/v1/intelligence/patterns/{pattern_id}/history', backend_tag='intelligence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetMarketPatternHistoryApiV1IntelligencePatternsPatternIdHistoryGetSuccess, security=GETMARKETPATTERNHISTORYAPIV1INTELLIGENCEPATTERNSPATTERNIDHISTORYGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_market_pattern_history_api_v1_intelligence_patterns__pattern_id__history_get',
    response_media_type='application/json',
)
async def get_market_pattern_history_api_v1_intelligence_patterns__pattern_id__history_get(transport: HttpTransport, request: GetMarketPatternHistoryApiV1IntelligencePatternsPatternIdHistoryGetRequest) -> GetMarketPatternHistoryApiV1IntelligencePatternsPatternIdHistoryGetSuccess:
    return await transport.invoke(GETMARKETPATTERNHISTORYAPIV1INTELLIGENCEPATTERNSPATTERNIDHISTORYGET_OPERATION, path_parameters={'pattern_id': str(request.pattern_id)}, query_parameters={}, body=None)

class GetMarketPatternOccurrencesApiV1IntelligencePatternsPatternIdOccurrencesGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    pattern_id: str
    limit: int | None = None

class GetMarketPatternOccurrencesApiV1IntelligencePatternsPatternIdOccurrencesGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

GetMarketPatternOccurrencesApiV1IntelligencePatternsPatternIdOccurrencesGetError = SafeTransportError

GETMARKETPATTERNOCCURRENCESAPIV1INTELLIGENCEPATTERNSPATTERNIDOCCURRENCESGET_SECURITY = SecurityMetadata(
    identity='public:get_market_pattern_occurrences_api_v1_intelligence_patterns__pattern_id__occurrences_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_market_pattern_occurrences_api_v1_intelligence_patterns__pattern_id__occurrences_get', review_owner='Stage 1B0-R7',
)
GETMARKETPATTERNOCCURRENCESAPIV1INTELLIGENCEPATTERNSPATTERNIDOCCURRENCESGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0117', operation_id='get_market_pattern_occurrences_api_v1_intelligence_patterns__pattern_id__occurrences_get',
    method='GET', path='/api/v1/intelligence/patterns/{pattern_id}/occurrences', backend_tag='intelligence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetMarketPatternOccurrencesApiV1IntelligencePatternsPatternIdOccurrencesGetSuccess, security=GETMARKETPATTERNOCCURRENCESAPIV1INTELLIGENCEPATTERNSPATTERNIDOCCURRENCESGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_market_pattern_occurrences_api_v1_intelligence_patterns__pattern_id__occurrences_get',
    response_media_type='application/json',
)
async def get_market_pattern_occurrences_api_v1_intelligence_patterns__pattern_id__occurrences_get(transport: HttpTransport, request: GetMarketPatternOccurrencesApiV1IntelligencePatternsPatternIdOccurrencesGetRequest) -> GetMarketPatternOccurrencesApiV1IntelligencePatternsPatternIdOccurrencesGetSuccess:
    return await transport.invoke(GETMARKETPATTERNOCCURRENCESAPIV1INTELLIGENCEPATTERNSPATTERNIDOCCURRENCESGET_OPERATION, path_parameters={'pattern_id': str(request.pattern_id)}, query_parameters={'limit': serialize_query_value(request.limit)}, body=None)

class GetMarketPatternReactionProfileApiV1IntelligencePatternsPatternIdReactionProfileGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    pattern_id: str

class GetMarketPatternReactionProfileApiV1IntelligencePatternsPatternIdReactionProfileGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

GetMarketPatternReactionProfileApiV1IntelligencePatternsPatternIdReactionProfileGetError = SafeTransportError

GETMARKETPATTERNREACTIONPROFILEAPIV1INTELLIGENCEPATTERNSPATTERNIDREACTIONPROFILEGET_SECURITY = SecurityMetadata(
    identity='public:get_market_pattern_reaction_profile_api_v1_intelligence_patterns__pattern_id__reaction_profile_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_market_pattern_reaction_profile_api_v1_intelligence_patterns__pattern_id__reaction_profile_get', review_owner='Stage 1B0-R7',
)
GETMARKETPATTERNREACTIONPROFILEAPIV1INTELLIGENCEPATTERNSPATTERNIDREACTIONPROFILEGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0118', operation_id='get_market_pattern_reaction_profile_api_v1_intelligence_patterns__pattern_id__reaction_profile_get',
    method='GET', path='/api/v1/intelligence/patterns/{pattern_id}/reaction-profile', backend_tag='intelligence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetMarketPatternReactionProfileApiV1IntelligencePatternsPatternIdReactionProfileGetSuccess, security=GETMARKETPATTERNREACTIONPROFILEAPIV1INTELLIGENCEPATTERNSPATTERNIDREACTIONPROFILEGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_market_pattern_reaction_profile_api_v1_intelligence_patterns__pattern_id__reaction_profile_get',
    response_media_type='application/json',
)
async def get_market_pattern_reaction_profile_api_v1_intelligence_patterns__pattern_id__reaction_profile_get(transport: HttpTransport, request: GetMarketPatternReactionProfileApiV1IntelligencePatternsPatternIdReactionProfileGetRequest) -> GetMarketPatternReactionProfileApiV1IntelligencePatternsPatternIdReactionProfileGetSuccess:
    return await transport.invoke(GETMARKETPATTERNREACTIONPROFILEAPIV1INTELLIGENCEPATTERNSPATTERNIDREACTIONPROFILEGET_OPERATION, path_parameters={'pattern_id': str(request.pattern_id)}, query_parameters={}, body=None)

class GetMarketPatternStatisticsApiV1IntelligencePatternsPatternIdStatisticsGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    pattern_id: str

class GetMarketPatternStatisticsApiV1IntelligencePatternsPatternIdStatisticsGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

GetMarketPatternStatisticsApiV1IntelligencePatternsPatternIdStatisticsGetError = SafeTransportError

GETMARKETPATTERNSTATISTICSAPIV1INTELLIGENCEPATTERNSPATTERNIDSTATISTICSGET_SECURITY = SecurityMetadata(
    identity='public:get_market_pattern_statistics_api_v1_intelligence_patterns__pattern_id__statistics_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_market_pattern_statistics_api_v1_intelligence_patterns__pattern_id__statistics_get', review_owner='Stage 1B0-R7',
)
GETMARKETPATTERNSTATISTICSAPIV1INTELLIGENCEPATTERNSPATTERNIDSTATISTICSGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0119', operation_id='get_market_pattern_statistics_api_v1_intelligence_patterns__pattern_id__statistics_get',
    method='GET', path='/api/v1/intelligence/patterns/{pattern_id}/statistics', backend_tag='intelligence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetMarketPatternStatisticsApiV1IntelligencePatternsPatternIdStatisticsGetSuccess, security=GETMARKETPATTERNSTATISTICSAPIV1INTELLIGENCEPATTERNSPATTERNIDSTATISTICSGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_market_pattern_statistics_api_v1_intelligence_patterns__pattern_id__statistics_get',
    response_media_type='application/json',
)
async def get_market_pattern_statistics_api_v1_intelligence_patterns__pattern_id__statistics_get(transport: HttpTransport, request: GetMarketPatternStatisticsApiV1IntelligencePatternsPatternIdStatisticsGetRequest) -> GetMarketPatternStatisticsApiV1IntelligencePatternsPatternIdStatisticsGetSuccess:
    return await transport.invoke(GETMARKETPATTERNSTATISTICSAPIV1INTELLIGENCEPATTERNSPATTERNIDSTATISTICSGET_OPERATION, path_parameters={'pattern_id': str(request.pattern_id)}, query_parameters={}, body=None)

class GetFoundationReactionProfileApiV1IntelligenceReactionProfileEventIdGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    event_id: int

class GetFoundationReactionProfileApiV1IntelligenceReactionProfileEventIdGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

GetFoundationReactionProfileApiV1IntelligenceReactionProfileEventIdGetError = SafeTransportError

GETFOUNDATIONREACTIONPROFILEAPIV1INTELLIGENCEREACTIONPROFILEEVENTIDGET_SECURITY = SecurityMetadata(
    identity='public:get_foundation_reaction_profile_api_v1_intelligence_reaction_profile__event_id__get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_foundation_reaction_profile_api_v1_intelligence_reaction_profile__event_id__get', review_owner='Stage 1B0-R7',
)
GETFOUNDATIONREACTIONPROFILEAPIV1INTELLIGENCEREACTIONPROFILEEVENTIDGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0120', operation_id='get_foundation_reaction_profile_api_v1_intelligence_reaction_profile__event_id__get',
    method='GET', path='/api/v1/intelligence/reaction-profile/{event_id}', backend_tag='intelligence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetFoundationReactionProfileApiV1IntelligenceReactionProfileEventIdGetSuccess, security=GETFOUNDATIONREACTIONPROFILEAPIV1INTELLIGENCEREACTIONPROFILEEVENTIDGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_foundation_reaction_profile_api_v1_intelligence_reaction_profile__event_id__get',
    response_media_type='application/json',
)
async def get_foundation_reaction_profile_api_v1_intelligence_reaction_profile__event_id__get(transport: HttpTransport, request: GetFoundationReactionProfileApiV1IntelligenceReactionProfileEventIdGetRequest) -> GetFoundationReactionProfileApiV1IntelligenceReactionProfileEventIdGetSuccess:
    return await transport.invoke(GETFOUNDATIONREACTIONPROFILEAPIV1INTELLIGENCEREACTIONPROFILEEVENTIDGET_OPERATION, path_parameters={'event_id': str(request.event_id)}, query_parameters={}, body=None)

class GetFoundationSimilarEventsApiV1IntelligenceSimilarEventsEventIdGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    event_id: int
    limit: int | None = None

class GetFoundationSimilarEventsApiV1IntelligenceSimilarEventsEventIdGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

GetFoundationSimilarEventsApiV1IntelligenceSimilarEventsEventIdGetError = SafeTransportError

GETFOUNDATIONSIMILAREVENTSAPIV1INTELLIGENCESIMILAREVENTSEVENTIDGET_SECURITY = SecurityMetadata(
    identity='public:get_foundation_similar_events_api_v1_intelligence_similar_events__event_id__get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_foundation_similar_events_api_v1_intelligence_similar_events__event_id__get', review_owner='Stage 1B0-R7',
)
GETFOUNDATIONSIMILAREVENTSAPIV1INTELLIGENCESIMILAREVENTSEVENTIDGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0121', operation_id='get_foundation_similar_events_api_v1_intelligence_similar_events__event_id__get',
    method='GET', path='/api/v1/intelligence/similar-events/{event_id}', backend_tag='intelligence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetFoundationSimilarEventsApiV1IntelligenceSimilarEventsEventIdGetSuccess, security=GETFOUNDATIONSIMILAREVENTSAPIV1INTELLIGENCESIMILAREVENTSEVENTIDGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_foundation_similar_events_api_v1_intelligence_similar_events__event_id__get',
    response_media_type='application/json',
)
async def get_foundation_similar_events_api_v1_intelligence_similar_events__event_id__get(transport: HttpTransport, request: GetFoundationSimilarEventsApiV1IntelligenceSimilarEventsEventIdGetRequest) -> GetFoundationSimilarEventsApiV1IntelligenceSimilarEventsEventIdGetSuccess:
    return await transport.invoke(GETFOUNDATIONSIMILAREVENTSAPIV1INTELLIGENCESIMILAREVENTSEVENTIDGET_OPERATION, path_parameters={'event_id': str(request.event_id)}, query_parameters={'limit': serialize_query_value(request.limit)}, body=None)

class GetArticleSimilarityReportApiV1IntelligenceSimilarityArticlesArticleIdGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    article_id: int
    limit: int | None = None

class GetArticleSimilarityReportApiV1IntelligenceSimilarityArticlesArticleIdGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

GetArticleSimilarityReportApiV1IntelligenceSimilarityArticlesArticleIdGetError = SafeTransportError

GETARTICLESIMILARITYREPORTAPIV1INTELLIGENCESIMILARITYARTICLESARTICLEIDGET_SECURITY = SecurityMetadata(
    identity='public:get_article_similarity_report_api_v1_intelligence_similarity_articles__article_id__get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_article_similarity_report_api_v1_intelligence_similarity_articles__article_id__get', review_owner='Stage 1B0-R7',
)
GETARTICLESIMILARITYREPORTAPIV1INTELLIGENCESIMILARITYARTICLESARTICLEIDGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0122', operation_id='get_article_similarity_report_api_v1_intelligence_similarity_articles__article_id__get',
    method='GET', path='/api/v1/intelligence/similarity/articles/{article_id}', backend_tag='intelligence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetArticleSimilarityReportApiV1IntelligenceSimilarityArticlesArticleIdGetSuccess, security=GETARTICLESIMILARITYREPORTAPIV1INTELLIGENCESIMILARITYARTICLESARTICLEIDGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_article_similarity_report_api_v1_intelligence_similarity_articles__article_id__get',
    response_media_type='application/json',
)
async def get_article_similarity_report_api_v1_intelligence_similarity_articles__article_id__get(transport: HttpTransport, request: GetArticleSimilarityReportApiV1IntelligenceSimilarityArticlesArticleIdGetRequest) -> GetArticleSimilarityReportApiV1IntelligenceSimilarityArticlesArticleIdGetSuccess:
    return await transport.invoke(GETARTICLESIMILARITYREPORTAPIV1INTELLIGENCESIMILARITYARTICLESARTICLEIDGET_OPERATION, path_parameters={'article_id': str(request.article_id)}, query_parameters={'limit': serialize_query_value(request.limit)}, body=None)

class GetCandleSimilarityApiV1IntelligenceSimilarityCandleCandleIdGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    candle_id: int
    limit: int | None = None

class GetCandleSimilarityApiV1IntelligenceSimilarityCandleCandleIdGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

GetCandleSimilarityApiV1IntelligenceSimilarityCandleCandleIdGetError = SafeTransportError

GETCANDLESIMILARITYAPIV1INTELLIGENCESIMILARITYCANDLECANDLEIDGET_SECURITY = SecurityMetadata(
    identity='public:get_candle_similarity_api_v1_intelligence_similarity_candle__candle_id__get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_candle_similarity_api_v1_intelligence_similarity_candle__candle_id__get', review_owner='Stage 1B0-R7',
)
GETCANDLESIMILARITYAPIV1INTELLIGENCESIMILARITYCANDLECANDLEIDGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0123', operation_id='get_candle_similarity_api_v1_intelligence_similarity_candle__candle_id__get',
    method='GET', path='/api/v1/intelligence/similarity/candle/{candle_id}', backend_tag='intelligence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetCandleSimilarityApiV1IntelligenceSimilarityCandleCandleIdGetSuccess, security=GETCANDLESIMILARITYAPIV1INTELLIGENCESIMILARITYCANDLECANDLEIDGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_candle_similarity_api_v1_intelligence_similarity_candle__candle_id__get',
    response_media_type='application/json',
)
async def get_candle_similarity_api_v1_intelligence_similarity_candle__candle_id__get(transport: HttpTransport, request: GetCandleSimilarityApiV1IntelligenceSimilarityCandleCandleIdGetRequest) -> GetCandleSimilarityApiV1IntelligenceSimilarityCandleCandleIdGetSuccess:
    return await transport.invoke(GETCANDLESIMILARITYAPIV1INTELLIGENCESIMILARITYCANDLECANDLEIDGET_OPERATION, path_parameters={'candle_id': str(request.candle_id)}, query_parameters={'limit': serialize_query_value(request.limit)}, body=None)

class GetEventSimilarityApiV1IntelligenceSimilarityEventEventIdGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    event_id: int
    limit: int | None = None

class GetEventSimilarityApiV1IntelligenceSimilarityEventEventIdGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

GetEventSimilarityApiV1IntelligenceSimilarityEventEventIdGetError = SafeTransportError

GETEVENTSIMILARITYAPIV1INTELLIGENCESIMILARITYEVENTEVENTIDGET_SECURITY = SecurityMetadata(
    identity='public:get_event_similarity_api_v1_intelligence_similarity_event__event_id__get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_event_similarity_api_v1_intelligence_similarity_event__event_id__get', review_owner='Stage 1B0-R7',
)
GETEVENTSIMILARITYAPIV1INTELLIGENCESIMILARITYEVENTEVENTIDGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0124', operation_id='get_event_similarity_api_v1_intelligence_similarity_event__event_id__get',
    method='GET', path='/api/v1/intelligence/similarity/event/{event_id}', backend_tag='intelligence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetEventSimilarityApiV1IntelligenceSimilarityEventEventIdGetSuccess, security=GETEVENTSIMILARITYAPIV1INTELLIGENCESIMILARITYEVENTEVENTIDGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_event_similarity_api_v1_intelligence_similarity_event__event_id__get',
    response_media_type='application/json',
)
async def get_event_similarity_api_v1_intelligence_similarity_event__event_id__get(transport: HttpTransport, request: GetEventSimilarityApiV1IntelligenceSimilarityEventEventIdGetRequest) -> GetEventSimilarityApiV1IntelligenceSimilarityEventEventIdGetSuccess:
    return await transport.invoke(GETEVENTSIMILARITYAPIV1INTELLIGENCESIMILARITYEVENTEVENTIDGET_OPERATION, path_parameters={'event_id': str(request.event_id)}, query_parameters={'limit': serialize_query_value(request.limit)}, body=None)

class GetEventSimilarityReportApiV1IntelligenceSimilarityEventsEventIdGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    event_id: int
    limit: int | None = None

class GetEventSimilarityReportApiV1IntelligenceSimilarityEventsEventIdGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

GetEventSimilarityReportApiV1IntelligenceSimilarityEventsEventIdGetError = SafeTransportError

GETEVENTSIMILARITYREPORTAPIV1INTELLIGENCESIMILARITYEVENTSEVENTIDGET_SECURITY = SecurityMetadata(
    identity='public:get_event_similarity_report_api_v1_intelligence_similarity_events__event_id__get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_event_similarity_report_api_v1_intelligence_similarity_events__event_id__get', review_owner='Stage 1B0-R7',
)
GETEVENTSIMILARITYREPORTAPIV1INTELLIGENCESIMILARITYEVENTSEVENTIDGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0125', operation_id='get_event_similarity_report_api_v1_intelligence_similarity_events__event_id__get',
    method='GET', path='/api/v1/intelligence/similarity/events/{event_id}', backend_tag='intelligence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetEventSimilarityReportApiV1IntelligenceSimilarityEventsEventIdGetSuccess, security=GETEVENTSIMILARITYREPORTAPIV1INTELLIGENCESIMILARITYEVENTSEVENTIDGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_event_similarity_report_api_v1_intelligence_similarity_events__event_id__get',
    response_media_type='application/json',
)
async def get_event_similarity_report_api_v1_intelligence_similarity_events__event_id__get(transport: HttpTransport, request: GetEventSimilarityReportApiV1IntelligenceSimilarityEventsEventIdGetRequest) -> GetEventSimilarityReportApiV1IntelligenceSimilarityEventsEventIdGetSuccess:
    return await transport.invoke(GETEVENTSIMILARITYREPORTAPIV1INTELLIGENCESIMILARITYEVENTSEVENTIDGET_OPERATION, path_parameters={'event_id': str(request.event_id)}, query_parameters={'limit': serialize_query_value(request.limit)}, body=None)

class GetNewsSimilarityApiV1IntelligenceSimilarityNewsEventIdGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    event_id: int
    limit: int | None = None

class GetNewsSimilarityApiV1IntelligenceSimilarityNewsEventIdGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

GetNewsSimilarityApiV1IntelligenceSimilarityNewsEventIdGetError = SafeTransportError

GETNEWSSIMILARITYAPIV1INTELLIGENCESIMILARITYNEWSEVENTIDGET_SECURITY = SecurityMetadata(
    identity='public:get_news_similarity_api_v1_intelligence_similarity_news__event_id__get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_news_similarity_api_v1_intelligence_similarity_news__event_id__get', review_owner='Stage 1B0-R7',
)
GETNEWSSIMILARITYAPIV1INTELLIGENCESIMILARITYNEWSEVENTIDGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0126', operation_id='get_news_similarity_api_v1_intelligence_similarity_news__event_id__get',
    method='GET', path='/api/v1/intelligence/similarity/news/{event_id}', backend_tag='intelligence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetNewsSimilarityApiV1IntelligenceSimilarityNewsEventIdGetSuccess, security=GETNEWSSIMILARITYAPIV1INTELLIGENCESIMILARITYNEWSEVENTIDGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_news_similarity_api_v1_intelligence_similarity_news__event_id__get',
    response_media_type='application/json',
)
async def get_news_similarity_api_v1_intelligence_similarity_news__event_id__get(transport: HttpTransport, request: GetNewsSimilarityApiV1IntelligenceSimilarityNewsEventIdGetRequest) -> GetNewsSimilarityApiV1IntelligenceSimilarityNewsEventIdGetSuccess:
    return await transport.invoke(GETNEWSSIMILARITYAPIV1INTELLIGENCESIMILARITYNEWSEVENTIDGET_OPERATION, path_parameters={'event_id': str(request.event_id)}, query_parameters={'limit': serialize_query_value(request.limit)}, body=None)

class GetSignalSimilarityReportApiV1IntelligenceSimilaritySignalsSignalIdGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    signal_id: int
    limit: int | None = None

class GetSignalSimilarityReportApiV1IntelligenceSimilaritySignalsSignalIdGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

GetSignalSimilarityReportApiV1IntelligenceSimilaritySignalsSignalIdGetError = SafeTransportError

GETSIGNALSIMILARITYREPORTAPIV1INTELLIGENCESIMILARITYSIGNALSSIGNALIDGET_SECURITY = SecurityMetadata(
    identity='public:get_signal_similarity_report_api_v1_intelligence_similarity_signals__signal_id__get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_signal_similarity_report_api_v1_intelligence_similarity_signals__signal_id__get', review_owner='Stage 1B0-R7',
)
GETSIGNALSIMILARITYREPORTAPIV1INTELLIGENCESIMILARITYSIGNALSSIGNALIDGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0127', operation_id='get_signal_similarity_report_api_v1_intelligence_similarity_signals__signal_id__get',
    method='GET', path='/api/v1/intelligence/similarity/signals/{signal_id}', backend_tag='intelligence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetSignalSimilarityReportApiV1IntelligenceSimilaritySignalsSignalIdGetSuccess, security=GETSIGNALSIMILARITYREPORTAPIV1INTELLIGENCESIMILARITYSIGNALSSIGNALIDGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_signal_similarity_report_api_v1_intelligence_similarity_signals__signal_id__get',
    response_media_type='application/json',
)
async def get_signal_similarity_report_api_v1_intelligence_similarity_signals__signal_id__get(transport: HttpTransport, request: GetSignalSimilarityReportApiV1IntelligenceSimilaritySignalsSignalIdGetRequest) -> GetSignalSimilarityReportApiV1IntelligenceSimilaritySignalsSignalIdGetSuccess:
    return await transport.invoke(GETSIGNALSIMILARITYREPORTAPIV1INTELLIGENCESIMILARITYSIGNALSSIGNALIDGET_OPERATION, path_parameters={'signal_id': str(request.signal_id)}, query_parameters={'limit': serialize_query_value(request.limit)}, body=None)

class GetHistoricalSimilarityContextApiV1IntelligenceSimilarityEventIdGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    event_id: int
    limit: int | None = None

class GetHistoricalSimilarityContextApiV1IntelligenceSimilarityEventIdGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

GetHistoricalSimilarityContextApiV1IntelligenceSimilarityEventIdGetError = SafeTransportError

GETHISTORICALSIMILARITYCONTEXTAPIV1INTELLIGENCESIMILARITYEVENTIDGET_SECURITY = SecurityMetadata(
    identity='public:get_historical_similarity_context_api_v1_intelligence_similarity__event_id__get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_historical_similarity_context_api_v1_intelligence_similarity__event_id__get', review_owner='Stage 1B0-R7',
)
GETHISTORICALSIMILARITYCONTEXTAPIV1INTELLIGENCESIMILARITYEVENTIDGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0128', operation_id='get_historical_similarity_context_api_v1_intelligence_similarity__event_id__get',
    method='GET', path='/api/v1/intelligence/similarity/{event_id}', backend_tag='intelligence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetHistoricalSimilarityContextApiV1IntelligenceSimilarityEventIdGetSuccess, security=GETHISTORICALSIMILARITYCONTEXTAPIV1INTELLIGENCESIMILARITYEVENTIDGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_historical_similarity_context_api_v1_intelligence_similarity__event_id__get',
    response_media_type='application/json',
)
async def get_historical_similarity_context_api_v1_intelligence_similarity__event_id__get(transport: HttpTransport, request: GetHistoricalSimilarityContextApiV1IntelligenceSimilarityEventIdGetRequest) -> GetHistoricalSimilarityContextApiV1IntelligenceSimilarityEventIdGetSuccess:
    return await transport.invoke(GETHISTORICALSIMILARITYCONTEXTAPIV1INTELLIGENCESIMILARITYEVENTIDGET_OPERATION, path_parameters={'event_id': str(request.event_id)}, query_parameters={'limit': serialize_query_value(request.limit)}, body=None)

class GetHistoricalSimilarityMatchesApiV1IntelligenceSimilarityEventIdMatchesGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    event_id: int
    limit: int | None = None

class GetHistoricalSimilarityMatchesApiV1IntelligenceSimilarityEventIdMatchesGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

GetHistoricalSimilarityMatchesApiV1IntelligenceSimilarityEventIdMatchesGetError = SafeTransportError

GETHISTORICALSIMILARITYMATCHESAPIV1INTELLIGENCESIMILARITYEVENTIDMATCHESGET_SECURITY = SecurityMetadata(
    identity='public:get_historical_similarity_matches_api_v1_intelligence_similarity__event_id__matches_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_historical_similarity_matches_api_v1_intelligence_similarity__event_id__matches_get', review_owner='Stage 1B0-R7',
)
GETHISTORICALSIMILARITYMATCHESAPIV1INTELLIGENCESIMILARITYEVENTIDMATCHESGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0129', operation_id='get_historical_similarity_matches_api_v1_intelligence_similarity__event_id__matches_get',
    method='GET', path='/api/v1/intelligence/similarity/{event_id}/matches', backend_tag='intelligence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetHistoricalSimilarityMatchesApiV1IntelligenceSimilarityEventIdMatchesGetSuccess, security=GETHISTORICALSIMILARITYMATCHESAPIV1INTELLIGENCESIMILARITYEVENTIDMATCHESGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_historical_similarity_matches_api_v1_intelligence_similarity__event_id__matches_get',
    response_media_type='application/json',
)
async def get_historical_similarity_matches_api_v1_intelligence_similarity__event_id__matches_get(transport: HttpTransport, request: GetHistoricalSimilarityMatchesApiV1IntelligenceSimilarityEventIdMatchesGetRequest) -> GetHistoricalSimilarityMatchesApiV1IntelligenceSimilarityEventIdMatchesGetSuccess:
    return await transport.invoke(GETHISTORICALSIMILARITYMATCHESAPIV1INTELLIGENCESIMILARITYEVENTIDMATCHESGET_OPERATION, path_parameters={'event_id': str(request.event_id)}, query_parameters={'limit': serialize_query_value(request.limit)}, body=None)

class GetTimelineApiV1IntelligenceTimelineGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    event_type: str | None | None = None
    limit: int | None = None

class GetTimelineApiV1IntelligenceTimelineGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

GetTimelineApiV1IntelligenceTimelineGetError = SafeTransportError

GETTIMELINEAPIV1INTELLIGENCETIMELINEGET_SECURITY = SecurityMetadata(
    identity='public:get_timeline_api_v1_intelligence_timeline_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_timeline_api_v1_intelligence_timeline_get', review_owner='Stage 1B0-R7',
)
GETTIMELINEAPIV1INTELLIGENCETIMELINEGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0130', operation_id='get_timeline_api_v1_intelligence_timeline_get',
    method='GET', path='/api/v1/intelligence/timeline', backend_tag='intelligence-timeline',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetTimelineApiV1IntelligenceTimelineGetSuccess, security=GETTIMELINEAPIV1INTELLIGENCETIMELINEGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_timeline_api_v1_intelligence_timeline_get',
    response_media_type='application/json',
)
async def get_timeline_api_v1_intelligence_timeline_get(transport: HttpTransport, request: GetTimelineApiV1IntelligenceTimelineGetRequest) -> GetTimelineApiV1IntelligenceTimelineGetSuccess:
    return await transport.invoke(GETTIMELINEAPIV1INTELLIGENCETIMELINEGET_OPERATION, path_parameters={}, query_parameters={'event_type': serialize_query_value(request.event_type), 'limit': serialize_query_value(request.limit)}, body=None)

class GetContextApiV1IntelligenceTimelineContextTimelineEventIdGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    timeline_event_id: int

class GetContextApiV1IntelligenceTimelineContextTimelineEventIdGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

GetContextApiV1IntelligenceTimelineContextTimelineEventIdGetError = SafeTransportError

GETCONTEXTAPIV1INTELLIGENCETIMELINECONTEXTTIMELINEEVENTIDGET_SECURITY = SecurityMetadata(
    identity='public:get_context_api_v1_intelligence_timeline_context__timeline_event_id__get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_context_api_v1_intelligence_timeline_context__timeline_event_id__get', review_owner='Stage 1B0-R7',
)
GETCONTEXTAPIV1INTELLIGENCETIMELINECONTEXTTIMELINEEVENTIDGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0131', operation_id='get_context_api_v1_intelligence_timeline_context__timeline_event_id__get',
    method='GET', path='/api/v1/intelligence/timeline/context/{timeline_event_id}', backend_tag='intelligence-timeline',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetContextApiV1IntelligenceTimelineContextTimelineEventIdGetSuccess, security=GETCONTEXTAPIV1INTELLIGENCETIMELINECONTEXTTIMELINEEVENTIDGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_context_api_v1_intelligence_timeline_context__timeline_event_id__get',
    response_media_type='application/json',
)
async def get_context_api_v1_intelligence_timeline_context__timeline_event_id__get(transport: HttpTransport, request: GetContextApiV1IntelligenceTimelineContextTimelineEventIdGetRequest) -> GetContextApiV1IntelligenceTimelineContextTimelineEventIdGetSuccess:
    return await transport.invoke(GETCONTEXTAPIV1INTELLIGENCETIMELINECONTEXTTIMELINEEVENTIDGET_OPERATION, path_parameters={'timeline_event_id': str(request.timeline_event_id)}, query_parameters={}, body=None)

class GetTimelineDayApiV1IntelligenceTimelineDayGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    page: int | None = None
    page_size: int | None = None
    filter: str | None = None

class GetTimelineDayApiV1IntelligenceTimelineDayGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

GetTimelineDayApiV1IntelligenceTimelineDayGetError = SafeTransportError

GETTIMELINEDAYAPIV1INTELLIGENCETIMELINEDAYGET_SECURITY = SecurityMetadata(
    identity='public:get_timeline_day_api_v1_intelligence_timeline_day_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_timeline_day_api_v1_intelligence_timeline_day_get', review_owner='Stage 1B0-R7',
)
GETTIMELINEDAYAPIV1INTELLIGENCETIMELINEDAYGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0132', operation_id='get_timeline_day_api_v1_intelligence_timeline_day_get',
    method='GET', path='/api/v1/intelligence/timeline/day', backend_tag='intelligence-timeline',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetTimelineDayApiV1IntelligenceTimelineDayGetSuccess, security=GETTIMELINEDAYAPIV1INTELLIGENCETIMELINEDAYGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_timeline_day_api_v1_intelligence_timeline_day_get',
    response_media_type='application/json',
)
async def get_timeline_day_api_v1_intelligence_timeline_day_get(transport: HttpTransport, request: GetTimelineDayApiV1IntelligenceTimelineDayGetRequest) -> GetTimelineDayApiV1IntelligenceTimelineDayGetSuccess:
    return await transport.invoke(GETTIMELINEDAYAPIV1INTELLIGENCETIMELINEDAYGET_OPERATION, path_parameters={}, query_parameters={'page': serialize_query_value(request.page), 'page_size': serialize_query_value(request.page_size), 'filter': serialize_query_value(request.filter)}, body=None)

class GetTimelineHourApiV1IntelligenceTimelineHourGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    page: int | None = None
    page_size: int | None = None
    filter: str | None = None

class GetTimelineHourApiV1IntelligenceTimelineHourGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

GetTimelineHourApiV1IntelligenceTimelineHourGetError = SafeTransportError

GETTIMELINEHOURAPIV1INTELLIGENCETIMELINEHOURGET_SECURITY = SecurityMetadata(
    identity='public:get_timeline_hour_api_v1_intelligence_timeline_hour_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_timeline_hour_api_v1_intelligence_timeline_hour_get', review_owner='Stage 1B0-R7',
)
GETTIMELINEHOURAPIV1INTELLIGENCETIMELINEHOURGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0133', operation_id='get_timeline_hour_api_v1_intelligence_timeline_hour_get',
    method='GET', path='/api/v1/intelligence/timeline/hour', backend_tag='intelligence-timeline',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetTimelineHourApiV1IntelligenceTimelineHourGetSuccess, security=GETTIMELINEHOURAPIV1INTELLIGENCETIMELINEHOURGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_timeline_hour_api_v1_intelligence_timeline_hour_get',
    response_media_type='application/json',
)
async def get_timeline_hour_api_v1_intelligence_timeline_hour_get(transport: HttpTransport, request: GetTimelineHourApiV1IntelligenceTimelineHourGetRequest) -> GetTimelineHourApiV1IntelligenceTimelineHourGetSuccess:
    return await transport.invoke(GETTIMELINEHOURAPIV1INTELLIGENCETIMELINEHOURGET_OPERATION, path_parameters={}, query_parameters={'page': serialize_query_value(request.page), 'page_size': serialize_query_value(request.page_size), 'filter': serialize_query_value(request.filter)}, body=None)

class GetLatestApiV1IntelligenceTimelineLatestGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    limit: int | None = None

class GetLatestApiV1IntelligenceTimelineLatestGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

GetLatestApiV1IntelligenceTimelineLatestGetError = SafeTransportError

GETLATESTAPIV1INTELLIGENCETIMELINELATESTGET_SECURITY = SecurityMetadata(
    identity='public:get_latest_api_v1_intelligence_timeline_latest_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_latest_api_v1_intelligence_timeline_latest_get', review_owner='Stage 1B0-R7',
)
GETLATESTAPIV1INTELLIGENCETIMELINELATESTGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0134', operation_id='get_latest_api_v1_intelligence_timeline_latest_get',
    method='GET', path='/api/v1/intelligence/timeline/latest', backend_tag='intelligence-timeline',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetLatestApiV1IntelligenceTimelineLatestGetSuccess, security=GETLATESTAPIV1INTELLIGENCETIMELINELATESTGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_latest_api_v1_intelligence_timeline_latest_get',
    response_media_type='application/json',
)
async def get_latest_api_v1_intelligence_timeline_latest_get(transport: HttpTransport, request: GetLatestApiV1IntelligenceTimelineLatestGetRequest) -> GetLatestApiV1IntelligenceTimelineLatestGetSuccess:
    return await transport.invoke(GETLATESTAPIV1INTELLIGENCETIMELINELATESTGET_OPERATION, path_parameters={}, query_parameters={'limit': serialize_query_value(request.limit)}, body=None)

class CurrentNarrativesApiV1IntelligenceTimelineNarrativesCurrentGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    limit: int | None = None

class CurrentNarrativesApiV1IntelligenceTimelineNarrativesCurrentGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

CurrentNarrativesApiV1IntelligenceTimelineNarrativesCurrentGetError = SafeTransportError

CURRENTNARRATIVESAPIV1INTELLIGENCETIMELINENARRATIVESCURRENTGET_SECURITY = SecurityMetadata(
    identity='public:current_narratives_api_v1_intelligence_timeline_narratives_current_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='current_narratives_api_v1_intelligence_timeline_narratives_current_get', review_owner='Stage 1B0-R7',
)
CURRENTNARRATIVESAPIV1INTELLIGENCETIMELINENARRATIVESCURRENTGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0135', operation_id='current_narratives_api_v1_intelligence_timeline_narratives_current_get',
    method='GET', path='/api/v1/intelligence/timeline/narratives/current', backend_tag='intelligence-timeline',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=CurrentNarrativesApiV1IntelligenceTimelineNarrativesCurrentGetSuccess, security=CURRENTNARRATIVESAPIV1INTELLIGENCETIMELINENARRATIVESCURRENTGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:current_narratives_api_v1_intelligence_timeline_narratives_current_get',
    response_media_type='application/json',
)
async def current_narratives_api_v1_intelligence_timeline_narratives_current_get(transport: HttpTransport, request: CurrentNarrativesApiV1IntelligenceTimelineNarrativesCurrentGetRequest) -> CurrentNarrativesApiV1IntelligenceTimelineNarrativesCurrentGetSuccess:
    return await transport.invoke(CURRENTNARRATIVESAPIV1INTELLIGENCETIMELINENARRATIVESCURRENTGET_OPERATION, path_parameters={}, query_parameters={'limit': serialize_query_value(request.limit)}, body=None)

class HighConfidenceNewsImpactsApiV1IntelligenceTimelineNewsImpactsHighConfidenceGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    limit: int | None = None

class HighConfidenceNewsImpactsApiV1IntelligenceTimelineNewsImpactsHighConfidenceGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

HighConfidenceNewsImpactsApiV1IntelligenceTimelineNewsImpactsHighConfidenceGetError = SafeTransportError

HIGHCONFIDENCENEWSIMPACTSAPIV1INTELLIGENCETIMELINENEWSIMPACTSHIGHCONFIDENCEGET_SECURITY = SecurityMetadata(
    identity='public:high_confidence_news_impacts_api_v1_intelligence_timeline_news_impacts_high_confidence_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='high_confidence_news_impacts_api_v1_intelligence_timeline_news_impacts_high_confidence_get', review_owner='Stage 1B0-R7',
)
HIGHCONFIDENCENEWSIMPACTSAPIV1INTELLIGENCETIMELINENEWSIMPACTSHIGHCONFIDENCEGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0136', operation_id='high_confidence_news_impacts_api_v1_intelligence_timeline_news_impacts_high_confidence_get',
    method='GET', path='/api/v1/intelligence/timeline/news-impacts/high-confidence', backend_tag='intelligence-timeline',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=HighConfidenceNewsImpactsApiV1IntelligenceTimelineNewsImpactsHighConfidenceGetSuccess, security=HIGHCONFIDENCENEWSIMPACTSAPIV1INTELLIGENCETIMELINENEWSIMPACTSHIGHCONFIDENCEGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:high_confidence_news_impacts_api_v1_intelligence_timeline_news_impacts_high_confidence_get',
    response_media_type='application/json',
)
async def high_confidence_news_impacts_api_v1_intelligence_timeline_news_impacts_high_confidence_get(transport: HttpTransport, request: HighConfidenceNewsImpactsApiV1IntelligenceTimelineNewsImpactsHighConfidenceGetRequest) -> HighConfidenceNewsImpactsApiV1IntelligenceTimelineNewsImpactsHighConfidenceGetSuccess:
    return await transport.invoke(HIGHCONFIDENCENEWSIMPACTSAPIV1INTELLIGENCETIMELINENEWSIMPACTSHIGHCONFIDENCEGET_OPERATION, path_parameters={}, query_parameters={'limit': serialize_query_value(request.limit)}, body=None)

class RecentNewsImpactsApiV1IntelligenceTimelineNewsImpactsRecentGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    limit: int | None = None

class RecentNewsImpactsApiV1IntelligenceTimelineNewsImpactsRecentGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

RecentNewsImpactsApiV1IntelligenceTimelineNewsImpactsRecentGetError = SafeTransportError

RECENTNEWSIMPACTSAPIV1INTELLIGENCETIMELINENEWSIMPACTSRECENTGET_SECURITY = SecurityMetadata(
    identity='public:recent_news_impacts_api_v1_intelligence_timeline_news_impacts_recent_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='recent_news_impacts_api_v1_intelligence_timeline_news_impacts_recent_get', review_owner='Stage 1B0-R7',
)
RECENTNEWSIMPACTSAPIV1INTELLIGENCETIMELINENEWSIMPACTSRECENTGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0137', operation_id='recent_news_impacts_api_v1_intelligence_timeline_news_impacts_recent_get',
    method='GET', path='/api/v1/intelligence/timeline/news-impacts/recent', backend_tag='intelligence-timeline',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=RecentNewsImpactsApiV1IntelligenceTimelineNewsImpactsRecentGetSuccess, security=RECENTNEWSIMPACTSAPIV1INTELLIGENCETIMELINENEWSIMPACTSRECENTGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:recent_news_impacts_api_v1_intelligence_timeline_news_impacts_recent_get',
    response_media_type='application/json',
)
async def recent_news_impacts_api_v1_intelligence_timeline_news_impacts_recent_get(transport: HttpTransport, request: RecentNewsImpactsApiV1IntelligenceTimelineNewsImpactsRecentGetRequest) -> RecentNewsImpactsApiV1IntelligenceTimelineNewsImpactsRecentGetSuccess:
    return await transport.invoke(RECENTNEWSIMPACTSAPIV1INTELLIGENCETIMELINENEWSIMPACTSRECENTGET_OPERATION, path_parameters={}, query_parameters={'limit': serialize_query_value(request.limit)}, body=None)

class GetWindowApiV1IntelligenceTimelineWindowGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    start: str
    end: str
    limit: int | None = None

class GetWindowApiV1IntelligenceTimelineWindowGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

GetWindowApiV1IntelligenceTimelineWindowGetError = SafeTransportError

GETWINDOWAPIV1INTELLIGENCETIMELINEWINDOWGET_SECURITY = SecurityMetadata(
    identity='public:get_window_api_v1_intelligence_timeline_window_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_window_api_v1_intelligence_timeline_window_get', review_owner='Stage 1B0-R7',
)
GETWINDOWAPIV1INTELLIGENCETIMELINEWINDOWGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0138', operation_id='get_window_api_v1_intelligence_timeline_window_get',
    method='GET', path='/api/v1/intelligence/timeline/window', backend_tag='intelligence-timeline',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetWindowApiV1IntelligenceTimelineWindowGetSuccess, security=GETWINDOWAPIV1INTELLIGENCETIMELINEWINDOWGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_window_api_v1_intelligence_timeline_window_get',
    response_media_type='application/json',
)
async def get_window_api_v1_intelligence_timeline_window_get(transport: HttpTransport, request: GetWindowApiV1IntelligenceTimelineWindowGetRequest) -> GetWindowApiV1IntelligenceTimelineWindowGetSuccess:
    return await transport.invoke(GETWINDOWAPIV1INTELLIGENCETIMELINEWINDOWGET_OPERATION, path_parameters={}, query_parameters={'start': serialize_query_value(request.start), 'end': serialize_query_value(request.end), 'limit': serialize_query_value(request.limit)}, body=None)

class CandleAttributionApiV1MarketTimeMachineCandleAttributionGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    from_ts: datetime | None | None = None
    to_ts: datetime | None | None = None
    asset: str | None = None
    interval: str | None = None
    limit: int | None = None

class CandleAttributionApiV1MarketTimeMachineCandleAttributionGetSuccess(RootModel[MarketTimeMachineAnalyticsResponse]):
    pass

CandleAttributionApiV1MarketTimeMachineCandleAttributionGetError = SafeTransportError

CANDLEATTRIBUTIONAPIV1MARKETTIMEMACHINECANDLEATTRIBUTIONGET_SECURITY = SecurityMetadata(
    identity='public:candle_attribution_api_v1_market_time_machine_candle_attribution_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='candle_attribution_api_v1_market_time_machine_candle_attribution_get', review_owner='Stage 1B0-R7',
)
CANDLEATTRIBUTIONAPIV1MARKETTIMEMACHINECANDLEATTRIBUTIONGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0142', operation_id='candle_attribution_api_v1_market_time_machine_candle_attribution_get',
    method='GET', path='/api/v1/market-time-machine/candle-attribution', backend_tag='market-time-machine',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=CandleAttributionApiV1MarketTimeMachineCandleAttributionGetSuccess, security=CANDLEATTRIBUTIONAPIV1MARKETTIMEMACHINECANDLEATTRIBUTIONGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:candle_attribution_api_v1_market_time_machine_candle_attribution_get',
    response_media_type='application/json',
)
async def candle_attribution_api_v1_market_time_machine_candle_attribution_get(transport: HttpTransport, request: CandleAttributionApiV1MarketTimeMachineCandleAttributionGetRequest) -> CandleAttributionApiV1MarketTimeMachineCandleAttributionGetSuccess:
    return await transport.invoke(CANDLEATTRIBUTIONAPIV1MARKETTIMEMACHINECANDLEATTRIBUTIONGET_OPERATION, path_parameters={}, query_parameters={'from_ts': serialize_query_value(request.from_ts), 'to_ts': serialize_query_value(request.to_ts), 'asset': serialize_query_value(request.asset), 'interval': serialize_query_value(request.interval), 'limit': serialize_query_value(request.limit)}, body=None)

class MarketEventsApiV1MarketTimeMachineEventsGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    from_ts: datetime | None | None = None
    to_ts: datetime | None | None = None
    asset: str | None = None
    limit: int | None = None
    event_type: str | None | None = None

class MarketEventsApiV1MarketTimeMachineEventsGetSuccess(RootModel[MarketTimeMachineAnalyticsResponse]):
    pass

MarketEventsApiV1MarketTimeMachineEventsGetError = SafeTransportError

MARKETEVENTSAPIV1MARKETTIMEMACHINEEVENTSGET_SECURITY = SecurityMetadata(
    identity='public:market_events_api_v1_market_time_machine_events_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='market_events_api_v1_market_time_machine_events_get', review_owner='Stage 1B0-R7',
)
MARKETEVENTSAPIV1MARKETTIMEMACHINEEVENTSGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0143', operation_id='market_events_api_v1_market_time_machine_events_get',
    method='GET', path='/api/v1/market-time-machine/events', backend_tag='market-time-machine',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=MarketEventsApiV1MarketTimeMachineEventsGetSuccess, security=MARKETEVENTSAPIV1MARKETTIMEMACHINEEVENTSGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:market_events_api_v1_market_time_machine_events_get',
    response_media_type='application/json',
)
async def market_events_api_v1_market_time_machine_events_get(transport: HttpTransport, request: MarketEventsApiV1MarketTimeMachineEventsGetRequest) -> MarketEventsApiV1MarketTimeMachineEventsGetSuccess:
    return await transport.invoke(MARKETEVENTSAPIV1MARKETTIMEMACHINEEVENTSGET_OPERATION, path_parameters={}, query_parameters={'from_ts': serialize_query_value(request.from_ts), 'to_ts': serialize_query_value(request.to_ts), 'asset': serialize_query_value(request.asset), 'limit': serialize_query_value(request.limit), 'event_type': serialize_query_value(request.event_type)}, body=None)

class NewsImpactApiV1MarketTimeMachineNewsImpactGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    from_ts: datetime | None | None = None
    to_ts: datetime | None | None = None
    asset: str | None = None
    source: str | None | None = None
    limit: int | None = None

class NewsImpactApiV1MarketTimeMachineNewsImpactGetSuccess(RootModel[MarketTimeMachineAnalyticsResponse]):
    pass

NewsImpactApiV1MarketTimeMachineNewsImpactGetError = SafeTransportError

NEWSIMPACTAPIV1MARKETTIMEMACHINENEWSIMPACTGET_SECURITY = SecurityMetadata(
    identity='public:news_impact_api_v1_market_time_machine_news_impact_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='news_impact_api_v1_market_time_machine_news_impact_get', review_owner='Stage 1B0-R7',
)
NEWSIMPACTAPIV1MARKETTIMEMACHINENEWSIMPACTGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0144', operation_id='news_impact_api_v1_market_time_machine_news_impact_get',
    method='GET', path='/api/v1/market-time-machine/news-impact', backend_tag='market-time-machine',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=NewsImpactApiV1MarketTimeMachineNewsImpactGetSuccess, security=NEWSIMPACTAPIV1MARKETTIMEMACHINENEWSIMPACTGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:news_impact_api_v1_market_time_machine_news_impact_get',
    response_media_type='application/json',
)
async def news_impact_api_v1_market_time_machine_news_impact_get(transport: HttpTransport, request: NewsImpactApiV1MarketTimeMachineNewsImpactGetRequest) -> NewsImpactApiV1MarketTimeMachineNewsImpactGetSuccess:
    return await transport.invoke(NEWSIMPACTAPIV1MARKETTIMEMACHINENEWSIMPACTGET_OPERATION, path_parameters={}, query_parameters={'from_ts': serialize_query_value(request.from_ts), 'to_ts': serialize_query_value(request.to_ts), 'asset': serialize_query_value(request.asset), 'source': serialize_query_value(request.source), 'limit': serialize_query_value(request.limit)}, body=None)

class ProviderDegradationApiV1MarketTimeMachineProviderDegradationGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    from_ts: datetime | None | None = None
    to_ts: datetime | None | None = None
    provider: str | None | None = None
    limit: int | None = None

class ProviderDegradationApiV1MarketTimeMachineProviderDegradationGetSuccess(RootModel[MarketTimeMachineAnalyticsResponse]):
    pass

ProviderDegradationApiV1MarketTimeMachineProviderDegradationGetError = SafeTransportError

PROVIDERDEGRADATIONAPIV1MARKETTIMEMACHINEPROVIDERDEGRADATIONGET_SECURITY = SecurityMetadata(
    identity='public:provider_degradation_api_v1_market_time_machine_provider_degradation_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='provider_degradation_api_v1_market_time_machine_provider_degradation_get', review_owner='Stage 1B0-R7',
)
PROVIDERDEGRADATIONAPIV1MARKETTIMEMACHINEPROVIDERDEGRADATIONGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0145', operation_id='provider_degradation_api_v1_market_time_machine_provider_degradation_get',
    method='GET', path='/api/v1/market-time-machine/provider-degradation', backend_tag='market-time-machine',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=ProviderDegradationApiV1MarketTimeMachineProviderDegradationGetSuccess, security=PROVIDERDEGRADATIONAPIV1MARKETTIMEMACHINEPROVIDERDEGRADATIONGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:provider_degradation_api_v1_market_time_machine_provider_degradation_get',
    response_media_type='application/json',
)
async def provider_degradation_api_v1_market_time_machine_provider_degradation_get(transport: HttpTransport, request: ProviderDegradationApiV1MarketTimeMachineProviderDegradationGetRequest) -> ProviderDegradationApiV1MarketTimeMachineProviderDegradationGetSuccess:
    return await transport.invoke(PROVIDERDEGRADATIONAPIV1MARKETTIMEMACHINEPROVIDERDEGRADATIONGET_OPERATION, path_parameters={}, query_parameters={'from_ts': serialize_query_value(request.from_ts), 'to_ts': serialize_query_value(request.to_ts), 'provider': serialize_query_value(request.provider), 'limit': serialize_query_value(request.limit)}, body=None)

class ReactionWindowsApiV1MarketTimeMachineReactionWindowsGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    from_ts: datetime | None | None = None
    to_ts: datetime | None | None = None
    asset: str | None = None
    source: str | None | None = None
    limit: int | None = None

class ReactionWindowsApiV1MarketTimeMachineReactionWindowsGetSuccess(RootModel[MarketTimeMachineAnalyticsResponse]):
    pass

ReactionWindowsApiV1MarketTimeMachineReactionWindowsGetError = SafeTransportError

REACTIONWINDOWSAPIV1MARKETTIMEMACHINEREACTIONWINDOWSGET_SECURITY = SecurityMetadata(
    identity='public:reaction_windows_api_v1_market_time_machine_reaction_windows_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='reaction_windows_api_v1_market_time_machine_reaction_windows_get', review_owner='Stage 1B0-R7',
)
REACTIONWINDOWSAPIV1MARKETTIMEMACHINEREACTIONWINDOWSGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0146', operation_id='reaction_windows_api_v1_market_time_machine_reaction_windows_get',
    method='GET', path='/api/v1/market-time-machine/reaction-windows', backend_tag='market-time-machine',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=ReactionWindowsApiV1MarketTimeMachineReactionWindowsGetSuccess, security=REACTIONWINDOWSAPIV1MARKETTIMEMACHINEREACTIONWINDOWSGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:reaction_windows_api_v1_market_time_machine_reaction_windows_get',
    response_media_type='application/json',
)
async def reaction_windows_api_v1_market_time_machine_reaction_windows_get(transport: HttpTransport, request: ReactionWindowsApiV1MarketTimeMachineReactionWindowsGetRequest) -> ReactionWindowsApiV1MarketTimeMachineReactionWindowsGetSuccess:
    return await transport.invoke(REACTIONWINDOWSAPIV1MARKETTIMEMACHINEREACTIONWINDOWSGET_OPERATION, path_parameters={}, query_parameters={'from_ts': serialize_query_value(request.from_ts), 'to_ts': serialize_query_value(request.to_ts), 'asset': serialize_query_value(request.asset), 'source': serialize_query_value(request.source), 'limit': serialize_query_value(request.limit)}, body=None)

class RegimeTransitionsApiV1MarketTimeMachineRegimeTransitionsGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    from_ts: datetime | None | None = None
    to_ts: datetime | None | None = None
    asset: str | None = None
    regime: str | None | None = None
    limit: int | None = None

class RegimeTransitionsApiV1MarketTimeMachineRegimeTransitionsGetSuccess(RootModel[MarketTimeMachineAnalyticsResponse]):
    pass

RegimeTransitionsApiV1MarketTimeMachineRegimeTransitionsGetError = SafeTransportError

REGIMETRANSITIONSAPIV1MARKETTIMEMACHINEREGIMETRANSITIONSGET_SECURITY = SecurityMetadata(
    identity='public:regime_transitions_api_v1_market_time_machine_regime_transitions_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='regime_transitions_api_v1_market_time_machine_regime_transitions_get', review_owner='Stage 1B0-R7',
)
REGIMETRANSITIONSAPIV1MARKETTIMEMACHINEREGIMETRANSITIONSGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0147', operation_id='regime_transitions_api_v1_market_time_machine_regime_transitions_get',
    method='GET', path='/api/v1/market-time-machine/regime-transitions', backend_tag='market-time-machine',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=RegimeTransitionsApiV1MarketTimeMachineRegimeTransitionsGetSuccess, security=REGIMETRANSITIONSAPIV1MARKETTIMEMACHINEREGIMETRANSITIONSGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:regime_transitions_api_v1_market_time_machine_regime_transitions_get',
    response_media_type='application/json',
)
async def regime_transitions_api_v1_market_time_machine_regime_transitions_get(transport: HttpTransport, request: RegimeTransitionsApiV1MarketTimeMachineRegimeTransitionsGetRequest) -> RegimeTransitionsApiV1MarketTimeMachineRegimeTransitionsGetSuccess:
    return await transport.invoke(REGIMETRANSITIONSAPIV1MARKETTIMEMACHINEREGIMETRANSITIONSGET_OPERATION, path_parameters={}, query_parameters={'from_ts': serialize_query_value(request.from_ts), 'to_ts': serialize_query_value(request.to_ts), 'asset': serialize_query_value(request.asset), 'regime': serialize_query_value(request.regime), 'limit': serialize_query_value(request.limit)}, body=None)

class SignalReliabilityApiV1MarketTimeMachineSignalReliabilityGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    from_ts: datetime | None | None = None
    to_ts: datetime | None | None = None
    asset: str | None = None
    min_confidence: Decimal | None | None = None
    limit: int | None = None

class SignalReliabilityApiV1MarketTimeMachineSignalReliabilityGetSuccess(RootModel[MarketTimeMachineAnalyticsResponse]):
    pass

SignalReliabilityApiV1MarketTimeMachineSignalReliabilityGetError = SafeTransportError

SIGNALRELIABILITYAPIV1MARKETTIMEMACHINESIGNALRELIABILITYGET_SECURITY = SecurityMetadata(
    identity='public:signal_reliability_api_v1_market_time_machine_signal_reliability_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='signal_reliability_api_v1_market_time_machine_signal_reliability_get', review_owner='Stage 1B0-R7',
)
SIGNALRELIABILITYAPIV1MARKETTIMEMACHINESIGNALRELIABILITYGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0148', operation_id='signal_reliability_api_v1_market_time_machine_signal_reliability_get',
    method='GET', path='/api/v1/market-time-machine/signal-reliability', backend_tag='market-time-machine',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=SignalReliabilityApiV1MarketTimeMachineSignalReliabilityGetSuccess, security=SIGNALRELIABILITYAPIV1MARKETTIMEMACHINESIGNALRELIABILITYGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:signal_reliability_api_v1_market_time_machine_signal_reliability_get',
    response_media_type='application/json',
)
async def signal_reliability_api_v1_market_time_machine_signal_reliability_get(transport: HttpTransport, request: SignalReliabilityApiV1MarketTimeMachineSignalReliabilityGetRequest) -> SignalReliabilityApiV1MarketTimeMachineSignalReliabilityGetSuccess:
    return await transport.invoke(SIGNALRELIABILITYAPIV1MARKETTIMEMACHINESIGNALRELIABILITYGET_OPERATION, path_parameters={}, query_parameters={'from_ts': serialize_query_value(request.from_ts), 'to_ts': serialize_query_value(request.to_ts), 'asset': serialize_query_value(request.asset), 'min_confidence': serialize_query_value(request.min_confidence), 'limit': serialize_query_value(request.limit)}, body=None)

class BtcCandlesApiV1MarketBtcCandlesGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    timeframe: str
    start: str | None | None = None
    end: str | None | None = None
    limit: int | None = None

class BtcCandlesApiV1MarketBtcCandlesGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

BtcCandlesApiV1MarketBtcCandlesGetError = SafeTransportError

BTCCANDLESAPIV1MARKETBTCCANDLESGET_SECURITY = SecurityMetadata(
    identity='public:btc_candles_api_v1_market_btc_candles_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='btc_candles_api_v1_market_btc_candles_get', review_owner='Stage 1B0-R7',
)
BTCCANDLESAPIV1MARKETBTCCANDLESGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0149', operation_id='btc_candles_api_v1_market_btc_candles_get',
    method='GET', path='/api/v1/market/btc/candles', backend_tag='market',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=BtcCandlesApiV1MarketBtcCandlesGetSuccess, security=BTCCANDLESAPIV1MARKETBTCCANDLESGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:btc_candles_api_v1_market_btc_candles_get',
    response_media_type='application/json',
)
async def btc_candles_api_v1_market_btc_candles_get(transport: HttpTransport, request: BtcCandlesApiV1MarketBtcCandlesGetRequest) -> BtcCandlesApiV1MarketBtcCandlesGetSuccess:
    return await transport.invoke(BTCCANDLESAPIV1MARKETBTCCANDLESGET_OPERATION, path_parameters={}, query_parameters={'timeframe': serialize_query_value(request.timeframe), 'start': serialize_query_value(request.start), 'end': serialize_query_value(request.end), 'limit': serialize_query_value(request.limit)}, body=None)

class BtcCandlesLatestAnyApiV1MarketBtcCandlesLatestGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    timeframe: str | None = None

class BtcCandlesLatestAnyApiV1MarketBtcCandlesLatestGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

BtcCandlesLatestAnyApiV1MarketBtcCandlesLatestGetError = SafeTransportError

BTCCANDLESLATESTANYAPIV1MARKETBTCCANDLESLATESTGET_SECURITY = SecurityMetadata(
    identity='public:btc_candles_latest_any_api_v1_market_btc_candles_latest_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='btc_candles_latest_any_api_v1_market_btc_candles_latest_get', review_owner='Stage 1B0-R7',
)
BTCCANDLESLATESTANYAPIV1MARKETBTCCANDLESLATESTGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0150', operation_id='btc_candles_latest_any_api_v1_market_btc_candles_latest_get',
    method='GET', path='/api/v1/market/btc/candles/latest', backend_tag='market',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=BtcCandlesLatestAnyApiV1MarketBtcCandlesLatestGetSuccess, security=BTCCANDLESLATESTANYAPIV1MARKETBTCCANDLESLATESTGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:btc_candles_latest_any_api_v1_market_btc_candles_latest_get',
    response_media_type='application/json',
)
async def btc_candles_latest_any_api_v1_market_btc_candles_latest_get(transport: HttpTransport, request: BtcCandlesLatestAnyApiV1MarketBtcCandlesLatestGetRequest) -> BtcCandlesLatestAnyApiV1MarketBtcCandlesLatestGetSuccess:
    return await transport.invoke(BTCCANDLESLATESTANYAPIV1MARKETBTCCANDLESLATESTGET_OPERATION, path_parameters={}, query_parameters={'timeframe': serialize_query_value(request.timeframe)}, body=None)

class BtcCandleByIdApiV1MarketBtcCandlesCandleIdGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    candle_id: int

class BtcCandleByIdApiV1MarketBtcCandlesCandleIdGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

BtcCandleByIdApiV1MarketBtcCandlesCandleIdGetError = SafeTransportError

BTCCANDLEBYIDAPIV1MARKETBTCCANDLESCANDLEIDGET_SECURITY = SecurityMetadata(
    identity='public:btc_candle_by_id_api_v1_market_btc_candles__candle_id__get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='btc_candle_by_id_api_v1_market_btc_candles__candle_id__get', review_owner='Stage 1B0-R7',
)
BTCCANDLEBYIDAPIV1MARKETBTCCANDLESCANDLEIDGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0151', operation_id='btc_candle_by_id_api_v1_market_btc_candles__candle_id__get',
    method='GET', path='/api/v1/market/btc/candles/{candle_id}', backend_tag='market',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=BtcCandleByIdApiV1MarketBtcCandlesCandleIdGetSuccess, security=BTCCANDLEBYIDAPIV1MARKETBTCCANDLESCANDLEIDGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:btc_candle_by_id_api_v1_market_btc_candles__candle_id__get',
    response_media_type='application/json',
)
async def btc_candle_by_id_api_v1_market_btc_candles__candle_id__get(transport: HttpTransport, request: BtcCandleByIdApiV1MarketBtcCandlesCandleIdGetRequest) -> BtcCandleByIdApiV1MarketBtcCandlesCandleIdGetSuccess:
    return await transport.invoke(BTCCANDLEBYIDAPIV1MARKETBTCCANDLESCANDLEIDGET_OPERATION, path_parameters={'candle_id': str(request.candle_id)}, query_parameters={}, body=None)

class BtcCandleEvidenceApiV1MarketBtcCandlesCandleIdEvidenceGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    candle_id: int

class BtcCandleEvidenceApiV1MarketBtcCandlesCandleIdEvidenceGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

BtcCandleEvidenceApiV1MarketBtcCandlesCandleIdEvidenceGetError = SafeTransportError

BTCCANDLEEVIDENCEAPIV1MARKETBTCCANDLESCANDLEIDEVIDENCEGET_SECURITY = SecurityMetadata(
    identity='public:btc_candle_evidence_api_v1_market_btc_candles__candle_id__evidence_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='btc_candle_evidence_api_v1_market_btc_candles__candle_id__evidence_get', review_owner='Stage 1B0-R7',
)
BTCCANDLEEVIDENCEAPIV1MARKETBTCCANDLESCANDLEIDEVIDENCEGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0152', operation_id='btc_candle_evidence_api_v1_market_btc_candles__candle_id__evidence_get',
    method='GET', path='/api/v1/market/btc/candles/{candle_id}/evidence', backend_tag='market',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=BtcCandleEvidenceApiV1MarketBtcCandlesCandleIdEvidenceGetSuccess, security=BTCCANDLEEVIDENCEAPIV1MARKETBTCCANDLESCANDLEIDEVIDENCEGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:btc_candle_evidence_api_v1_market_btc_candles__candle_id__evidence_get',
    response_media_type='application/json',
)
async def btc_candle_evidence_api_v1_market_btc_candles__candle_id__evidence_get(transport: HttpTransport, request: BtcCandleEvidenceApiV1MarketBtcCandlesCandleIdEvidenceGetRequest) -> BtcCandleEvidenceApiV1MarketBtcCandlesCandleIdEvidenceGetSuccess:
    return await transport.invoke(BTCCANDLEEVIDENCEAPIV1MARKETBTCCANDLESCANDLEIDEVIDENCEGET_OPERATION, path_parameters={'candle_id': str(request.candle_id)}, query_parameters={}, body=None)

class BtcCandlesLatestApiV1MarketBtcCandlesTimeframeLatestGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    timeframe: str

class BtcCandlesLatestApiV1MarketBtcCandlesTimeframeLatestGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

BtcCandlesLatestApiV1MarketBtcCandlesTimeframeLatestGetError = SafeTransportError

BTCCANDLESLATESTAPIV1MARKETBTCCANDLESTIMEFRAMELATESTGET_SECURITY = SecurityMetadata(
    identity='public:btc_candles_latest_api_v1_market_btc_candles__timeframe__latest_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='btc_candles_latest_api_v1_market_btc_candles__timeframe__latest_get', review_owner='Stage 1B0-R7',
)
BTCCANDLESLATESTAPIV1MARKETBTCCANDLESTIMEFRAMELATESTGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0153', operation_id='btc_candles_latest_api_v1_market_btc_candles__timeframe__latest_get',
    method='GET', path='/api/v1/market/btc/candles/{timeframe}/latest', backend_tag='market',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=BtcCandlesLatestApiV1MarketBtcCandlesTimeframeLatestGetSuccess, security=BTCCANDLESLATESTAPIV1MARKETBTCCANDLESTIMEFRAMELATESTGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:btc_candles_latest_api_v1_market_btc_candles__timeframe__latest_get',
    response_media_type='application/json',
)
async def btc_candles_latest_api_v1_market_btc_candles__timeframe__latest_get(transport: HttpTransport, request: BtcCandlesLatestApiV1MarketBtcCandlesTimeframeLatestGetRequest) -> BtcCandlesLatestApiV1MarketBtcCandlesTimeframeLatestGetSuccess:
    return await transport.invoke(BTCCANDLESLATESTAPIV1MARKETBTCCANDLESTIMEFRAMELATESTGET_OPERATION, path_parameters={'timeframe': str(request.timeframe)}, query_parameters={}, body=None)

class BtcContextApiV1MarketBtcContextGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    pass

class BtcContextApiV1MarketBtcContextGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

BtcContextApiV1MarketBtcContextGetError = SafeTransportError

BTCCONTEXTAPIV1MARKETBTCCONTEXTGET_SECURITY = SecurityMetadata(
    identity='public:btc_context_api_v1_market_btc_context_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='btc_context_api_v1_market_btc_context_get', review_owner='Stage 1B0-R7',
)
BTCCONTEXTAPIV1MARKETBTCCONTEXTGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0154', operation_id='btc_context_api_v1_market_btc_context_get',
    method='GET', path='/api/v1/market/btc/context', backend_tag='market',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=BtcContextApiV1MarketBtcContextGetSuccess, security=BTCCONTEXTAPIV1MARKETBTCCONTEXTGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:btc_context_api_v1_market_btc_context_get',
    response_media_type='application/json',
)
async def btc_context_api_v1_market_btc_context_get(transport: HttpTransport, request: BtcContextApiV1MarketBtcContextGetRequest) -> BtcContextApiV1MarketBtcContextGetSuccess:
    return await transport.invoke(BTCCONTEXTAPIV1MARKETBTCCONTEXTGET_OPERATION, path_parameters={}, query_parameters={}, body=None)

class BtcPriceApiV1MarketBtcPriceGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    pass

class BtcPriceApiV1MarketBtcPriceGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

BtcPriceApiV1MarketBtcPriceGetError = SafeTransportError

BTCPRICEAPIV1MARKETBTCPRICEGET_SECURITY = SecurityMetadata(
    identity='public:btc_price_api_v1_market_btc_price_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='btc_price_api_v1_market_btc_price_get', review_owner='Stage 1B0-R7',
)
BTCPRICEAPIV1MARKETBTCPRICEGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0155', operation_id='btc_price_api_v1_market_btc_price_get',
    method='GET', path='/api/v1/market/btc/price', backend_tag='market',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=BtcPriceApiV1MarketBtcPriceGetSuccess, security=BTCPRICEAPIV1MARKETBTCPRICEGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:btc_price_api_v1_market_btc_price_get',
    response_media_type='application/json',
)
async def btc_price_api_v1_market_btc_price_get(transport: HttpTransport, request: BtcPriceApiV1MarketBtcPriceGetRequest) -> BtcPriceApiV1MarketBtcPriceGetSuccess:
    return await transport.invoke(BTCPRICEAPIV1MARKETBTCPRICEGET_OPERATION, path_parameters={}, query_parameters={}, body=None)

class BtcPriceHistoryApiV1MarketBtcPriceHistoryGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    limit: int | None = None

class BtcPriceHistoryApiV1MarketBtcPriceHistoryGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

BtcPriceHistoryApiV1MarketBtcPriceHistoryGetError = SafeTransportError

BTCPRICEHISTORYAPIV1MARKETBTCPRICEHISTORYGET_SECURITY = SecurityMetadata(
    identity='public:btc_price_history_api_v1_market_btc_price_history_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='btc_price_history_api_v1_market_btc_price_history_get', review_owner='Stage 1B0-R7',
)
BTCPRICEHISTORYAPIV1MARKETBTCPRICEHISTORYGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0156', operation_id='btc_price_history_api_v1_market_btc_price_history_get',
    method='GET', path='/api/v1/market/btc/price/history', backend_tag='market',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=BtcPriceHistoryApiV1MarketBtcPriceHistoryGetSuccess, security=BTCPRICEHISTORYAPIV1MARKETBTCPRICEHISTORYGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:btc_price_history_api_v1_market_btc_price_history_get',
    response_media_type='application/json',
)
async def btc_price_history_api_v1_market_btc_price_history_get(transport: HttpTransport, request: BtcPriceHistoryApiV1MarketBtcPriceHistoryGetRequest) -> BtcPriceHistoryApiV1MarketBtcPriceHistoryGetSuccess:
    return await transport.invoke(BTCPRICEHISTORYAPIV1MARKETBTCPRICEHISTORYGET_OPERATION, path_parameters={}, query_parameters={'limit': serialize_query_value(request.limit)}, body=None)

class BtcProvidersApiV1MarketBtcProvidersGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    pass

class BtcProvidersApiV1MarketBtcProvidersGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

BtcProvidersApiV1MarketBtcProvidersGetError = SafeTransportError

BTCPROVIDERSAPIV1MARKETBTCPROVIDERSGET_SECURITY = SecurityMetadata(
    identity='public:btc_providers_api_v1_market_btc_providers_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='btc_providers_api_v1_market_btc_providers_get', review_owner='Stage 1B0-R7',
)
BTCPROVIDERSAPIV1MARKETBTCPROVIDERSGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0157', operation_id='btc_providers_api_v1_market_btc_providers_get',
    method='GET', path='/api/v1/market/btc/providers', backend_tag='market',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=BtcProvidersApiV1MarketBtcProvidersGetSuccess, security=BTCPROVIDERSAPIV1MARKETBTCPROVIDERSGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:btc_providers_api_v1_market_btc_providers_get',
    response_media_type='application/json',
)
async def btc_providers_api_v1_market_btc_providers_get(transport: HttpTransport, request: BtcProvidersApiV1MarketBtcProvidersGetRequest) -> BtcProvidersApiV1MarketBtcProvidersGetSuccess:
    return await transport.invoke(BTCPROVIDERSAPIV1MARKETBTCPROVIDERSGET_OPERATION, path_parameters={}, query_parameters={}, body=None)

class BtcProvidersHealthApiV1MarketBtcProvidersHealthGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    pass

class BtcProvidersHealthApiV1MarketBtcProvidersHealthGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

BtcProvidersHealthApiV1MarketBtcProvidersHealthGetError = SafeTransportError

BTCPROVIDERSHEALTHAPIV1MARKETBTCPROVIDERSHEALTHGET_SECURITY = SecurityMetadata(
    identity='public:btc_providers_health_api_v1_market_btc_providers_health_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='btc_providers_health_api_v1_market_btc_providers_health_get', review_owner='Stage 1B0-R7',
)
BTCPROVIDERSHEALTHAPIV1MARKETBTCPROVIDERSHEALTHGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0158', operation_id='btc_providers_health_api_v1_market_btc_providers_health_get',
    method='GET', path='/api/v1/market/btc/providers/health', backend_tag='market-data',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=BtcProvidersHealthApiV1MarketBtcProvidersHealthGetSuccess, security=BTCPROVIDERSHEALTHAPIV1MARKETBTCPROVIDERSHEALTHGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:btc_providers_health_api_v1_market_btc_providers_health_get',
    response_media_type='application/json',
)
async def btc_providers_health_api_v1_market_btc_providers_health_get(transport: HttpTransport, request: BtcProvidersHealthApiV1MarketBtcProvidersHealthGetRequest) -> BtcProvidersHealthApiV1MarketBtcProvidersHealthGetSuccess:
    return await transport.invoke(BTCPROVIDERSHEALTHAPIV1MARKETBTCPROVIDERSHEALTHGET_OPERATION, path_parameters={}, query_parameters={}, body=None)

class MarketHealthApiV1MarketHealthGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    pass

class MarketHealthApiV1MarketHealthGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

MarketHealthApiV1MarketHealthGetError = SafeTransportError

MARKETHEALTHAPIV1MARKETHEALTHGET_SECURITY = SecurityMetadata(
    identity='public:market_health_api_v1_market_health_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='market_health_api_v1_market_health_get', review_owner='Stage 1B0-R7',
)
MARKETHEALTHAPIV1MARKETHEALTHGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0159', operation_id='market_health_api_v1_market_health_get',
    method='GET', path='/api/v1/market/health', backend_tag='market',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=MarketHealthApiV1MarketHealthGetSuccess, security=MARKETHEALTHAPIV1MARKETHEALTHGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:market_health_api_v1_market_health_get',
    response_media_type='application/json',
)
async def market_health_api_v1_market_health_get(transport: HttpTransport, request: MarketHealthApiV1MarketHealthGetRequest) -> MarketHealthApiV1MarketHealthGetSuccess:
    return await transport.invoke(MARKETHEALTHAPIV1MARKETHEALTHGET_OPERATION, path_parameters={}, query_parameters={}, body=None)

class ProvidersHealthApiV1MarketProvidersHealthGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    pass

class ProvidersHealthApiV1MarketProvidersHealthGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

ProvidersHealthApiV1MarketProvidersHealthGetError = SafeTransportError

PROVIDERSHEALTHAPIV1MARKETPROVIDERSHEALTHGET_SECURITY = SecurityMetadata(
    identity='public:providers_health_api_v1_market_providers_health_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='providers_health_api_v1_market_providers_health_get', review_owner='Stage 1B0-R7',
)
PROVIDERSHEALTHAPIV1MARKETPROVIDERSHEALTHGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0160', operation_id='providers_health_api_v1_market_providers_health_get',
    method='GET', path='/api/v1/market/providers/health', backend_tag='market',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=ProvidersHealthApiV1MarketProvidersHealthGetSuccess, security=PROVIDERSHEALTHAPIV1MARKETPROVIDERSHEALTHGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:providers_health_api_v1_market_providers_health_get',
    response_media_type='application/json',
)
async def providers_health_api_v1_market_providers_health_get(transport: HttpTransport, request: ProvidersHealthApiV1MarketProvidersHealthGetRequest) -> ProvidersHealthApiV1MarketProvidersHealthGetSuccess:
    return await transport.invoke(PROVIDERSHEALTHAPIV1MARKETPROVIDERSHEALTHGET_OPERATION, path_parameters={}, query_parameters={}, body=None)

class ArticleDuplicatesApiV1NewsArticlesArticleIdDuplicatesGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    article_id: int

class ArticleDuplicatesApiV1NewsArticlesArticleIdDuplicatesGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

ArticleDuplicatesApiV1NewsArticlesArticleIdDuplicatesGetError = SafeTransportError

ARTICLEDUPLICATESAPIV1NEWSARTICLESARTICLEIDDUPLICATESGET_SECURITY = SecurityMetadata(
    identity='public:article_duplicates_api_v1_news_articles__article_id__duplicates_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='article_duplicates_api_v1_news_articles__article_id__duplicates_get', review_owner='Stage 1B0-R7',
)
ARTICLEDUPLICATESAPIV1NEWSARTICLESARTICLEIDDUPLICATESGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0167', operation_id='article_duplicates_api_v1_news_articles__article_id__duplicates_get',
    method='GET', path='/api/v1/news/articles/{article_id}/duplicates', backend_tag='market-intelligence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=ArticleDuplicatesApiV1NewsArticlesArticleIdDuplicatesGetSuccess, security=ARTICLEDUPLICATESAPIV1NEWSARTICLESARTICLEIDDUPLICATESGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:article_duplicates_api_v1_news_articles__article_id__duplicates_get',
    response_media_type='application/json',
)
async def article_duplicates_api_v1_news_articles__article_id__duplicates_get(transport: HttpTransport, request: ArticleDuplicatesApiV1NewsArticlesArticleIdDuplicatesGetRequest) -> ArticleDuplicatesApiV1NewsArticlesArticleIdDuplicatesGetSuccess:
    return await transport.invoke(ARTICLEDUPLICATESAPIV1NEWSARTICLESARTICLEIDDUPLICATESGET_OPERATION, path_parameters={'article_id': str(request.article_id)}, query_parameters={}, body=None)

class BySentimentApiV1NewsBySentimentLabelGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    label: str
    limit: int | None = None

class BySentimentApiV1NewsBySentimentLabelGetSuccess(RootModel[ResponseEnvelopeListDictStrObject]):
    pass

BySentimentApiV1NewsBySentimentLabelGetError = SafeTransportError

BYSENTIMENTAPIV1NEWSBYSENTIMENTLABELGET_SECURITY = SecurityMetadata(
    identity='public:by_sentiment_api_v1_news_by_sentiment__label__get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='by_sentiment_api_v1_news_by_sentiment__label__get', review_owner='Stage 1B0-R7',
)
BYSENTIMENTAPIV1NEWSBYSENTIMENTLABELGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0168', operation_id='by_sentiment_api_v1_news_by_sentiment__label__get',
    method='GET', path='/api/v1/news/by-sentiment/{label}', backend_tag='news',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=BySentimentApiV1NewsBySentimentLabelGetSuccess, security=BYSENTIMENTAPIV1NEWSBYSENTIMENTLABELGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:by_sentiment_api_v1_news_by_sentiment__label__get',
    response_media_type='application/json',
)
async def by_sentiment_api_v1_news_by_sentiment__label__get(transport: HttpTransport, request: BySentimentApiV1NewsBySentimentLabelGetRequest) -> BySentimentApiV1NewsBySentimentLabelGetSuccess:
    return await transport.invoke(BYSENTIMENTAPIV1NEWSBYSENTIMENTLABELGET_OPERATION, path_parameters={'label': str(request.label)}, query_parameters={'limit': serialize_query_value(request.limit)}, body=None)

class ListClustersApiV1NewsClustersGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    pass

class ListClustersApiV1NewsClustersGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

ListClustersApiV1NewsClustersGetError = SafeTransportError

LISTCLUSTERSAPIV1NEWSCLUSTERSGET_SECURITY = SecurityMetadata(
    identity='public:list_clusters_api_v1_news_clusters_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='list_clusters_api_v1_news_clusters_get', review_owner='Stage 1B0-R7',
)
LISTCLUSTERSAPIV1NEWSCLUSTERSGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0169', operation_id='list_clusters_api_v1_news_clusters_get',
    method='GET', path='/api/v1/news/clusters', backend_tag='market-intelligence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=ListClustersApiV1NewsClustersGetSuccess, security=LISTCLUSTERSAPIV1NEWSCLUSTERSGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:list_clusters_api_v1_news_clusters_get',
    response_media_type='application/json',
)
async def list_clusters_api_v1_news_clusters_get(transport: HttpTransport, request: ListClustersApiV1NewsClustersGetRequest) -> ListClustersApiV1NewsClustersGetSuccess:
    return await transport.invoke(LISTCLUSTERSAPIV1NEWSCLUSTERSGET_OPERATION, path_parameters={}, query_parameters={}, body=None)

class GetClusterApiV1NewsClustersClusterIdGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    cluster_id: int

class GetClusterApiV1NewsClustersClusterIdGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

GetClusterApiV1NewsClustersClusterIdGetError = SafeTransportError

GETCLUSTERAPIV1NEWSCLUSTERSCLUSTERIDGET_SECURITY = SecurityMetadata(
    identity='public:get_cluster_api_v1_news_clusters__cluster_id__get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_cluster_api_v1_news_clusters__cluster_id__get', review_owner='Stage 1B0-R7',
)
GETCLUSTERAPIV1NEWSCLUSTERSCLUSTERIDGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0170', operation_id='get_cluster_api_v1_news_clusters__cluster_id__get',
    method='GET', path='/api/v1/news/clusters/{cluster_id}', backend_tag='market-intelligence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetClusterApiV1NewsClustersClusterIdGetSuccess, security=GETCLUSTERAPIV1NEWSCLUSTERSCLUSTERIDGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_cluster_api_v1_news_clusters__cluster_id__get',
    response_media_type='application/json',
)
async def get_cluster_api_v1_news_clusters__cluster_id__get(transport: HttpTransport, request: GetClusterApiV1NewsClustersClusterIdGetRequest) -> GetClusterApiV1NewsClustersClusterIdGetSuccess:
    return await transport.invoke(GETCLUSTERAPIV1NEWSCLUSTERSCLUSTERIDGET_OPERATION, path_parameters={'cluster_id': str(request.cluster_id)}, query_parameters={}, body=None)

class ListEventsApiV1NewsEventsGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    pass

class ListEventsApiV1NewsEventsGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

ListEventsApiV1NewsEventsGetError = SafeTransportError

LISTEVENTSAPIV1NEWSEVENTSGET_SECURITY = SecurityMetadata(
    identity='public:list_events_api_v1_news_events_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='list_events_api_v1_news_events_get', review_owner='Stage 1B0-R7',
)
LISTEVENTSAPIV1NEWSEVENTSGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0171', operation_id='list_events_api_v1_news_events_get',
    method='GET', path='/api/v1/news/events', backend_tag='market-intelligence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=ListEventsApiV1NewsEventsGetSuccess, security=LISTEVENTSAPIV1NEWSEVENTSGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:list_events_api_v1_news_events_get',
    response_media_type='application/json',
)
async def list_events_api_v1_news_events_get(transport: HttpTransport, request: ListEventsApiV1NewsEventsGetRequest) -> ListEventsApiV1NewsEventsGetSuccess:
    return await transport.invoke(LISTEVENTSAPIV1NEWSEVENTSGET_OPERATION, path_parameters={}, query_parameters={}, body=None)

class HighImpactEventsApiV1NewsEventsHighImpactGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    pass

class HighImpactEventsApiV1NewsEventsHighImpactGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

HighImpactEventsApiV1NewsEventsHighImpactGetError = SafeTransportError

HIGHIMPACTEVENTSAPIV1NEWSEVENTSHIGHIMPACTGET_SECURITY = SecurityMetadata(
    identity='public:high_impact_events_api_v1_news_events_high_impact_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='high_impact_events_api_v1_news_events_high_impact_get', review_owner='Stage 1B0-R7',
)
HIGHIMPACTEVENTSAPIV1NEWSEVENTSHIGHIMPACTGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0172', operation_id='high_impact_events_api_v1_news_events_high_impact_get',
    method='GET', path='/api/v1/news/events/high-impact', backend_tag='market-intelligence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=HighImpactEventsApiV1NewsEventsHighImpactGetSuccess, security=HIGHIMPACTEVENTSAPIV1NEWSEVENTSHIGHIMPACTGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:high_impact_events_api_v1_news_events_high_impact_get',
    response_media_type='application/json',
)
async def high_impact_events_api_v1_news_events_high_impact_get(transport: HttpTransport, request: HighImpactEventsApiV1NewsEventsHighImpactGetRequest) -> HighImpactEventsApiV1NewsEventsHighImpactGetSuccess:
    return await transport.invoke(HIGHIMPACTEVENTSAPIV1NEWSEVENTSHIGHIMPACTGET_OPERATION, path_parameters={}, query_parameters={}, body=None)

class RegulatoryEventsApiV1NewsEventsRegulatoryGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    pass

class RegulatoryEventsApiV1NewsEventsRegulatoryGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

RegulatoryEventsApiV1NewsEventsRegulatoryGetError = SafeTransportError

REGULATORYEVENTSAPIV1NEWSEVENTSREGULATORYGET_SECURITY = SecurityMetadata(
    identity='public:regulatory_events_api_v1_news_events_regulatory_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='regulatory_events_api_v1_news_events_regulatory_get', review_owner='Stage 1B0-R7',
)
REGULATORYEVENTSAPIV1NEWSEVENTSREGULATORYGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0173', operation_id='regulatory_events_api_v1_news_events_regulatory_get',
    method='GET', path='/api/v1/news/events/regulatory', backend_tag='market-intelligence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=RegulatoryEventsApiV1NewsEventsRegulatoryGetSuccess, security=REGULATORYEVENTSAPIV1NEWSEVENTSREGULATORYGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:regulatory_events_api_v1_news_events_regulatory_get',
    response_media_type='application/json',
)
async def regulatory_events_api_v1_news_events_regulatory_get(transport: HttpTransport, request: RegulatoryEventsApiV1NewsEventsRegulatoryGetRequest) -> RegulatoryEventsApiV1NewsEventsRegulatoryGetSuccess:
    return await transport.invoke(REGULATORYEVENTSAPIV1NEWSEVENTSREGULATORYGET_OPERATION, path_parameters={}, query_parameters={}, body=None)

class SecurityEventsApiV1NewsEventsSecurityGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    pass

class SecurityEventsApiV1NewsEventsSecurityGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

SecurityEventsApiV1NewsEventsSecurityGetError = SafeTransportError

SECURITYEVENTSAPIV1NEWSEVENTSSECURITYGET_SECURITY = SecurityMetadata(
    identity='public:security_events_api_v1_news_events_security_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='security_events_api_v1_news_events_security_get', review_owner='Stage 1B0-R7',
)
SECURITYEVENTSAPIV1NEWSEVENTSSECURITYGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0174', operation_id='security_events_api_v1_news_events_security_get',
    method='GET', path='/api/v1/news/events/security', backend_tag='market-intelligence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=SecurityEventsApiV1NewsEventsSecurityGetSuccess, security=SECURITYEVENTSAPIV1NEWSEVENTSSECURITYGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:security_events_api_v1_news_events_security_get',
    response_media_type='application/json',
)
async def security_events_api_v1_news_events_security_get(transport: HttpTransport, request: SecurityEventsApiV1NewsEventsSecurityGetRequest) -> SecurityEventsApiV1NewsEventsSecurityGetSuccess:
    return await transport.invoke(SECURITYEVENTSAPIV1NEWSEVENTSSECURITYGET_OPERATION, path_parameters={}, query_parameters={}, body=None)

class GetEventApiV1NewsEventsEventIdGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    event_id: int

class GetEventApiV1NewsEventsEventIdGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

GetEventApiV1NewsEventsEventIdGetError = SafeTransportError

GETEVENTAPIV1NEWSEVENTSEVENTIDGET_SECURITY = SecurityMetadata(
    identity='public:get_event_api_v1_news_events__event_id__get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_event_api_v1_news_events__event_id__get', review_owner='Stage 1B0-R7',
)
GETEVENTAPIV1NEWSEVENTSEVENTIDGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0175', operation_id='get_event_api_v1_news_events__event_id__get',
    method='GET', path='/api/v1/news/events/{event_id}', backend_tag='market-intelligence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetEventApiV1NewsEventsEventIdGetSuccess, security=GETEVENTAPIV1NEWSEVENTSEVENTIDGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_event_api_v1_news_events__event_id__get',
    response_media_type='application/json',
)
async def get_event_api_v1_news_events__event_id__get(transport: HttpTransport, request: GetEventApiV1NewsEventsEventIdGetRequest) -> GetEventApiV1NewsEventsEventIdGetSuccess:
    return await transport.invoke(GETEVENTAPIV1NEWSEVENTSEVENTIDGET_OPERATION, path_parameters={'event_id': str(request.event_id)}, query_parameters={}, body=None)

class GetEventArticlesApiV1NewsEventsEventIdArticlesGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    event_id: int

class GetEventArticlesApiV1NewsEventsEventIdArticlesGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

GetEventArticlesApiV1NewsEventsEventIdArticlesGetError = SafeTransportError

GETEVENTARTICLESAPIV1NEWSEVENTSEVENTIDARTICLESGET_SECURITY = SecurityMetadata(
    identity='public:get_event_articles_api_v1_news_events__event_id__articles_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_event_articles_api_v1_news_events__event_id__articles_get', review_owner='Stage 1B0-R7',
)
GETEVENTARTICLESAPIV1NEWSEVENTSEVENTIDARTICLESGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0176', operation_id='get_event_articles_api_v1_news_events__event_id__articles_get',
    method='GET', path='/api/v1/news/events/{event_id}/articles', backend_tag='market-intelligence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetEventArticlesApiV1NewsEventsEventIdArticlesGetSuccess, security=GETEVENTARTICLESAPIV1NEWSEVENTSEVENTIDARTICLESGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_event_articles_api_v1_news_events__event_id__articles_get',
    response_media_type='application/json',
)
async def get_event_articles_api_v1_news_events__event_id__articles_get(transport: HttpTransport, request: GetEventArticlesApiV1NewsEventsEventIdArticlesGetRequest) -> GetEventArticlesApiV1NewsEventsEventIdArticlesGetSuccess:
    return await transport.invoke(GETEVENTARTICLESAPIV1NEWSEVENTSEVENTIDARTICLESGET_OPERATION, path_parameters={'event_id': str(request.event_id)}, query_parameters={}, body=None)

class GetEventImpactApiV1NewsEventsEventIdImpactGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    event_id: int

class GetEventImpactApiV1NewsEventsEventIdImpactGetSuccess(RootModel[ResponseEnvelopeDictStrObject]):
    pass

GetEventImpactApiV1NewsEventsEventIdImpactGetError = SafeTransportError

GETEVENTIMPACTAPIV1NEWSEVENTSEVENTIDIMPACTGET_SECURITY = SecurityMetadata(
    identity='public:get_event_impact_api_v1_news_events__event_id__impact_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_event_impact_api_v1_news_events__event_id__impact_get', review_owner='Stage 1B0-R7',
)
GETEVENTIMPACTAPIV1NEWSEVENTSEVENTIDIMPACTGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0177', operation_id='get_event_impact_api_v1_news_events__event_id__impact_get',
    method='GET', path='/api/v1/news/events/{event_id}/impact', backend_tag='news',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetEventImpactApiV1NewsEventsEventIdImpactGetSuccess, security=GETEVENTIMPACTAPIV1NEWSEVENTSEVENTIDIMPACTGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_event_impact_api_v1_news_events__event_id__impact_get',
    response_media_type='application/json',
)
async def get_event_impact_api_v1_news_events__event_id__impact_get(transport: HttpTransport, request: GetEventImpactApiV1NewsEventsEventIdImpactGetRequest) -> GetEventImpactApiV1NewsEventsEventIdImpactGetSuccess:
    return await transport.invoke(GETEVENTIMPACTAPIV1NEWSEVENTSEVENTIDIMPACTGET_OPERATION, path_parameters={'event_id': str(request.event_id)}, query_parameters={}, body=None)

class GetEventScoreApiV1NewsEventsEventIdScoreGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    event_id: int

class GetEventScoreApiV1NewsEventsEventIdScoreGetSuccess(RootModel[ResponseEnvelopeDictStrObject]):
    pass

GetEventScoreApiV1NewsEventsEventIdScoreGetError = SafeTransportError

GETEVENTSCOREAPIV1NEWSEVENTSEVENTIDSCOREGET_SECURITY = SecurityMetadata(
    identity='public:get_event_score_api_v1_news_events__event_id__score_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_event_score_api_v1_news_events__event_id__score_get', review_owner='Stage 1B0-R7',
)
GETEVENTSCOREAPIV1NEWSEVENTSEVENTIDSCOREGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0178', operation_id='get_event_score_api_v1_news_events__event_id__score_get',
    method='GET', path='/api/v1/news/events/{event_id}/score', backend_tag='news',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetEventScoreApiV1NewsEventsEventIdScoreGetSuccess, security=GETEVENTSCOREAPIV1NEWSEVENTSEVENTIDSCOREGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_event_score_api_v1_news_events__event_id__score_get',
    response_media_type='application/json',
)
async def get_event_score_api_v1_news_events__event_id__score_get(transport: HttpTransport, request: GetEventScoreApiV1NewsEventsEventIdScoreGetRequest) -> GetEventScoreApiV1NewsEventsEventIdScoreGetSuccess:
    return await transport.invoke(GETEVENTSCOREAPIV1NEWSEVENTSEVENTIDSCOREGET_OPERATION, path_parameters={'event_id': str(request.event_id)}, query_parameters={}, body=None)

class HighImpactNewsApiV1NewsHighImpactGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    limit: int | None = None

class HighImpactNewsApiV1NewsHighImpactGetSuccess(RootModel[ResponseEnvelopeListDictStrObject]):
    pass

HighImpactNewsApiV1NewsHighImpactGetError = SafeTransportError

HIGHIMPACTNEWSAPIV1NEWSHIGHIMPACTGET_SECURITY = SecurityMetadata(
    identity='public:high_impact_news_api_v1_news_high_impact_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='high_impact_news_api_v1_news_high_impact_get', review_owner='Stage 1B0-R7',
)
HIGHIMPACTNEWSAPIV1NEWSHIGHIMPACTGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0179', operation_id='high_impact_news_api_v1_news_high_impact_get',
    method='GET', path='/api/v1/news/high-impact', backend_tag='news',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=HighImpactNewsApiV1NewsHighImpactGetSuccess, security=HIGHIMPACTNEWSAPIV1NEWSHIGHIMPACTGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:high_impact_news_api_v1_news_high_impact_get',
    response_media_type='application/json',
)
async def high_impact_news_api_v1_news_high_impact_get(transport: HttpTransport, request: HighImpactNewsApiV1NewsHighImpactGetRequest) -> HighImpactNewsApiV1NewsHighImpactGetSuccess:
    return await transport.invoke(HIGHIMPACTNEWSAPIV1NEWSHIGHIMPACTGET_OPERATION, path_parameters={}, query_parameters={'limit': serialize_query_value(request.limit)}, body=None)

class HighRelevanceApiV1NewsHighRelevanceGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    limit: int | None = None

class HighRelevanceApiV1NewsHighRelevanceGetSuccess(RootModel[ResponseEnvelopeListDictStrObject]):
    pass

HighRelevanceApiV1NewsHighRelevanceGetError = SafeTransportError

HIGHRELEVANCEAPIV1NEWSHIGHRELEVANCEGET_SECURITY = SecurityMetadata(
    identity='public:high_relevance_api_v1_news_high_relevance_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='high_relevance_api_v1_news_high_relevance_get', review_owner='Stage 1B0-R7',
)
HIGHRELEVANCEAPIV1NEWSHIGHRELEVANCEGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0180', operation_id='high_relevance_api_v1_news_high_relevance_get',
    method='GET', path='/api/v1/news/high-relevance', backend_tag='news',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=HighRelevanceApiV1NewsHighRelevanceGetSuccess, security=HIGHRELEVANCEAPIV1NEWSHIGHRELEVANCEGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:high_relevance_api_v1_news_high_relevance_get',
    response_media_type='application/json',
)
async def high_relevance_api_v1_news_high_relevance_get(transport: HttpTransport, request: HighRelevanceApiV1NewsHighRelevanceGetRequest) -> HighRelevanceApiV1NewsHighRelevanceGetSuccess:
    return await transport.invoke(HIGHRELEVANCEAPIV1NEWSHIGHRELEVANCEGET_OPERATION, path_parameters={}, query_parameters={'limit': serialize_query_value(request.limit)}, body=None)

class LatestNewsApiV1NewsLatestGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    limit: int | None = None
    offset: int | None = None

class LatestNewsApiV1NewsLatestGetSuccess(RootModel[ResponseEnvelopePaginatedDataNewsArticleOut]):
    pass

LatestNewsApiV1NewsLatestGetError = SafeTransportError

LATESTNEWSAPIV1NEWSLATESTGET_SECURITY = SecurityMetadata(
    identity='public:latest_news_api_v1_news_latest_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='latest_news_api_v1_news_latest_get', review_owner='Stage 1B0-R7',
)
LATESTNEWSAPIV1NEWSLATESTGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0181', operation_id='latest_news_api_v1_news_latest_get',
    method='GET', path='/api/v1/news/latest', backend_tag='news',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=LatestNewsApiV1NewsLatestGetSuccess, security=LATESTNEWSAPIV1NEWSLATESTGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:latest_news_api_v1_news_latest_get',
    response_media_type='application/json',
)
async def latest_news_api_v1_news_latest_get(transport: HttpTransport, request: LatestNewsApiV1NewsLatestGetRequest) -> LatestNewsApiV1NewsLatestGetSuccess:
    return await transport.invoke(LATESTNEWSAPIV1NEWSLATESTGET_OPERATION, path_parameters={}, query_parameters={'limit': serialize_query_value(request.limit), 'offset': serialize_query_value(request.offset)}, body=None)

class RegulatoryNewsApiV1NewsRegulatoryGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    limit: int | None = None

class RegulatoryNewsApiV1NewsRegulatoryGetSuccess(RootModel[ResponseEnvelopeListDictStrObject]):
    pass

RegulatoryNewsApiV1NewsRegulatoryGetError = SafeTransportError

REGULATORYNEWSAPIV1NEWSREGULATORYGET_SECURITY = SecurityMetadata(
    identity='public:regulatory_news_api_v1_news_regulatory_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='regulatory_news_api_v1_news_regulatory_get', review_owner='Stage 1B0-R7',
)
REGULATORYNEWSAPIV1NEWSREGULATORYGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0182', operation_id='regulatory_news_api_v1_news_regulatory_get',
    method='GET', path='/api/v1/news/regulatory', backend_tag='news',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=RegulatoryNewsApiV1NewsRegulatoryGetSuccess, security=REGULATORYNEWSAPIV1NEWSREGULATORYGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:regulatory_news_api_v1_news_regulatory_get',
    response_media_type='application/json',
)
async def regulatory_news_api_v1_news_regulatory_get(transport: HttpTransport, request: RegulatoryNewsApiV1NewsRegulatoryGetRequest) -> RegulatoryNewsApiV1NewsRegulatoryGetSuccess:
    return await transport.invoke(REGULATORYNEWSAPIV1NEWSREGULATORYGET_OPERATION, path_parameters={}, query_parameters={'limit': serialize_query_value(request.limit)}, body=None)

class SecurityNewsApiV1NewsSecurityGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    limit: int | None = None

class SecurityNewsApiV1NewsSecurityGetSuccess(RootModel[ResponseEnvelopeListDictStrObject]):
    pass

SecurityNewsApiV1NewsSecurityGetError = SafeTransportError

SECURITYNEWSAPIV1NEWSSECURITYGET_SECURITY = SecurityMetadata(
    identity='public:security_news_api_v1_news_security_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='security_news_api_v1_news_security_get', review_owner='Stage 1B0-R7',
)
SECURITYNEWSAPIV1NEWSSECURITYGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0183', operation_id='security_news_api_v1_news_security_get',
    method='GET', path='/api/v1/news/security', backend_tag='news',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=SecurityNewsApiV1NewsSecurityGetSuccess, security=SECURITYNEWSAPIV1NEWSSECURITYGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:security_news_api_v1_news_security_get',
    response_media_type='application/json',
)
async def security_news_api_v1_news_security_get(transport: HttpTransport, request: SecurityNewsApiV1NewsSecurityGetRequest) -> SecurityNewsApiV1NewsSecurityGetSuccess:
    return await transport.invoke(SECURITYNEWSAPIV1NEWSSECURITYGET_OPERATION, path_parameters={}, query_parameters={'limit': serialize_query_value(request.limit)}, body=None)

class ListSourcesApiV1NewsSourcesGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    pass

class ListSourcesApiV1NewsSourcesGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

ListSourcesApiV1NewsSourcesGetError = SafeTransportError

LISTSOURCESAPIV1NEWSSOURCESGET_SECURITY = SecurityMetadata(
    identity='public:list_sources_api_v1_news_sources_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='list_sources_api_v1_news_sources_get', review_owner='Stage 1B0-R7',
)
LISTSOURCESAPIV1NEWSSOURCESGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0184', operation_id='list_sources_api_v1_news_sources_get',
    method='GET', path='/api/v1/news/sources', backend_tag='market-intelligence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=ListSourcesApiV1NewsSourcesGetSuccess, security=LISTSOURCESAPIV1NEWSSOURCESGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:list_sources_api_v1_news_sources_get',
    response_media_type='application/json',
)
async def list_sources_api_v1_news_sources_get(transport: HttpTransport, request: ListSourcesApiV1NewsSourcesGetRequest) -> ListSourcesApiV1NewsSourcesGetSuccess:
    return await transport.invoke(LISTSOURCESAPIV1NEWSSOURCESGET_OPERATION, path_parameters={}, query_parameters={}, body=None)

class CategoriesApiV1NewsSourcesCategoriesGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    pass

class CategoriesApiV1NewsSourcesCategoriesGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

CategoriesApiV1NewsSourcesCategoriesGetError = SafeTransportError

CATEGORIESAPIV1NEWSSOURCESCATEGORIESGET_SECURITY = SecurityMetadata(
    identity='public:categories_api_v1_news_sources_categories_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='categories_api_v1_news_sources_categories_get', review_owner='Stage 1B0-R7',
)
CATEGORIESAPIV1NEWSSOURCESCATEGORIESGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0185', operation_id='categories_api_v1_news_sources_categories_get',
    method='GET', path='/api/v1/news/sources/categories', backend_tag='market-intelligence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=CategoriesApiV1NewsSourcesCategoriesGetSuccess, security=CATEGORIESAPIV1NEWSSOURCESCATEGORIESGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:categories_api_v1_news_sources_categories_get',
    response_media_type='application/json',
)
async def categories_api_v1_news_sources_categories_get(transport: HttpTransport, request: CategoriesApiV1NewsSourcesCategoriesGetRequest) -> CategoriesApiV1NewsSourcesCategoriesGetSuccess:
    return await transport.invoke(CATEGORIESAPIV1NEWSSOURCESCATEGORIESGET_OPERATION, path_parameters={}, query_parameters={}, body=None)

class SourcesHealthApiV1NewsSourcesHealthGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    pass

class SourcesHealthApiV1NewsSourcesHealthGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

SourcesHealthApiV1NewsSourcesHealthGetError = SafeTransportError

SOURCESHEALTHAPIV1NEWSSOURCESHEALTHGET_SECURITY = SecurityMetadata(
    identity='public:sources_health_api_v1_news_sources_health_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='sources_health_api_v1_news_sources_health_get', review_owner='Stage 1B0-R7',
)
SOURCESHEALTHAPIV1NEWSSOURCESHEALTHGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0186', operation_id='sources_health_api_v1_news_sources_health_get',
    method='GET', path='/api/v1/news/sources/health', backend_tag='market-intelligence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=SourcesHealthApiV1NewsSourcesHealthGetSuccess, security=SOURCESHEALTHAPIV1NEWSSOURCESHEALTHGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:sources_health_api_v1_news_sources_health_get',
    response_media_type='application/json',
)
async def sources_health_api_v1_news_sources_health_get(transport: HttpTransport, request: SourcesHealthApiV1NewsSourcesHealthGetRequest) -> SourcesHealthApiV1NewsSourcesHealthGetSuccess:
    return await transport.invoke(SOURCESHEALTHAPIV1NEWSSOURCESHEALTHGET_OPERATION, path_parameters={}, query_parameters={}, body=None)

class ListSourceReputationApiV1NewsSourcesReputationGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    limit: int | None = None
    offset: int | None = None

class ListSourceReputationApiV1NewsSourcesReputationGetSuccess(RootModel[ResponseEnvelopeListSourceReputationProfileOut]):
    pass

ListSourceReputationApiV1NewsSourcesReputationGetError = SafeTransportError

LISTSOURCEREPUTATIONAPIV1NEWSSOURCESREPUTATIONGET_SECURITY = SecurityMetadata(
    identity='public:list_source_reputation_api_v1_news_sources_reputation_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='list_source_reputation_api_v1_news_sources_reputation_get', review_owner='Stage 1B0-R7',
)
LISTSOURCEREPUTATIONAPIV1NEWSSOURCESREPUTATIONGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0187', operation_id='list_source_reputation_api_v1_news_sources_reputation_get',
    method='GET', path='/api/v1/news/sources/reputation', backend_tag='news',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=ListSourceReputationApiV1NewsSourcesReputationGetSuccess, security=LISTSOURCEREPUTATIONAPIV1NEWSSOURCESREPUTATIONGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:list_source_reputation_api_v1_news_sources_reputation_get',
    response_media_type='application/json',
)
async def list_source_reputation_api_v1_news_sources_reputation_get(transport: HttpTransport, request: ListSourceReputationApiV1NewsSourcesReputationGetRequest) -> ListSourceReputationApiV1NewsSourcesReputationGetSuccess:
    return await transport.invoke(LISTSOURCEREPUTATIONAPIV1NEWSSOURCESREPUTATIONGET_OPERATION, path_parameters={}, query_parameters={'limit': serialize_query_value(request.limit), 'offset': serialize_query_value(request.offset)}, body=None)

class TiersApiV1NewsSourcesTiersGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    pass

class TiersApiV1NewsSourcesTiersGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

TiersApiV1NewsSourcesTiersGetError = SafeTransportError

TIERSAPIV1NEWSSOURCESTIERSGET_SECURITY = SecurityMetadata(
    identity='public:tiers_api_v1_news_sources_tiers_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='tiers_api_v1_news_sources_tiers_get', review_owner='Stage 1B0-R7',
)
TIERSAPIV1NEWSSOURCESTIERSGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0189', operation_id='tiers_api_v1_news_sources_tiers_get',
    method='GET', path='/api/v1/news/sources/tiers', backend_tag='market-intelligence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=TiersApiV1NewsSourcesTiersGetSuccess, security=TIERSAPIV1NEWSSOURCESTIERSGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:tiers_api_v1_news_sources_tiers_get',
    response_media_type='application/json',
)
async def tiers_api_v1_news_sources_tiers_get(transport: HttpTransport, request: TiersApiV1NewsSourcesTiersGetRequest) -> TiersApiV1NewsSourcesTiersGetSuccess:
    return await transport.invoke(TIERSAPIV1NEWSSOURCESTIERSGET_OPERATION, path_parameters={}, query_parameters={}, body=None)

class GetSourceApiV1NewsSourcesSourceIdGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    source_id: int

class GetSourceApiV1NewsSourcesSourceIdGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

GetSourceApiV1NewsSourcesSourceIdGetError = SafeTransportError

GETSOURCEAPIV1NEWSSOURCESSOURCEIDGET_SECURITY = SecurityMetadata(
    identity='public:get_source_api_v1_news_sources__source_id__get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_source_api_v1_news_sources__source_id__get', review_owner='Stage 1B0-R7',
)
GETSOURCEAPIV1NEWSSOURCESSOURCEIDGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0190', operation_id='get_source_api_v1_news_sources__source_id__get',
    method='GET', path='/api/v1/news/sources/{source_id}', backend_tag='market-intelligence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetSourceApiV1NewsSourcesSourceIdGetSuccess, security=GETSOURCEAPIV1NEWSSOURCESSOURCEIDGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_source_api_v1_news_sources__source_id__get',
    response_media_type='application/json',
)
async def get_source_api_v1_news_sources__source_id__get(transport: HttpTransport, request: GetSourceApiV1NewsSourcesSourceIdGetRequest) -> GetSourceApiV1NewsSourcesSourceIdGetSuccess:
    return await transport.invoke(GETSOURCEAPIV1NEWSSOURCESSOURCEIDGET_OPERATION, path_parameters={'source_id': str(request.source_id)}, query_parameters={}, body=None)

class SourceConfidenceEventsApiV1NewsSourcesSourceIdConfidenceEventsGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    source_id: int

class SourceConfidenceEventsApiV1NewsSourcesSourceIdConfidenceEventsGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

SourceConfidenceEventsApiV1NewsSourcesSourceIdConfidenceEventsGetError = SafeTransportError

SOURCECONFIDENCEEVENTSAPIV1NEWSSOURCESSOURCEIDCONFIDENCEEVENTSGET_SECURITY = SecurityMetadata(
    identity='public:source_confidence_events_api_v1_news_sources__source_id__confidence_events_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='source_confidence_events_api_v1_news_sources__source_id__confidence_events_get', review_owner='Stage 1B0-R7',
)
SOURCECONFIDENCEEVENTSAPIV1NEWSSOURCESSOURCEIDCONFIDENCEEVENTSGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0191', operation_id='source_confidence_events_api_v1_news_sources__source_id__confidence_events_get',
    method='GET', path='/api/v1/news/sources/{source_id}/confidence-events', backend_tag='market-intelligence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=SourceConfidenceEventsApiV1NewsSourcesSourceIdConfidenceEventsGetSuccess, security=SOURCECONFIDENCEEVENTSAPIV1NEWSSOURCESSOURCEIDCONFIDENCEEVENTSGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:source_confidence_events_api_v1_news_sources__source_id__confidence_events_get',
    response_media_type='application/json',
)
async def source_confidence_events_api_v1_news_sources__source_id__confidence_events_get(transport: HttpTransport, request: SourceConfidenceEventsApiV1NewsSourcesSourceIdConfidenceEventsGetRequest) -> SourceConfidenceEventsApiV1NewsSourcesSourceIdConfidenceEventsGetSuccess:
    return await transport.invoke(SOURCECONFIDENCEEVENTSAPIV1NEWSSOURCESSOURCEIDCONFIDENCEEVENTSGET_OPERATION, path_parameters={'source_id': str(request.source_id)}, query_parameters={}, body=None)

class SourceHealthApiV1NewsSourcesSourceIdHealthGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    source_id: int

class SourceHealthApiV1NewsSourcesSourceIdHealthGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

SourceHealthApiV1NewsSourcesSourceIdHealthGetError = SafeTransportError

SOURCEHEALTHAPIV1NEWSSOURCESSOURCEIDHEALTHGET_SECURITY = SecurityMetadata(
    identity='public:source_health_api_v1_news_sources__source_id__health_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='source_health_api_v1_news_sources__source_id__health_get', review_owner='Stage 1B0-R7',
)
SOURCEHEALTHAPIV1NEWSSOURCESSOURCEIDHEALTHGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0192', operation_id='source_health_api_v1_news_sources__source_id__health_get',
    method='GET', path='/api/v1/news/sources/{source_id}/health', backend_tag='market-intelligence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=SourceHealthApiV1NewsSourcesSourceIdHealthGetSuccess, security=SOURCEHEALTHAPIV1NEWSSOURCESSOURCEIDHEALTHGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:source_health_api_v1_news_sources__source_id__health_get',
    response_media_type='application/json',
)
async def source_health_api_v1_news_sources__source_id__health_get(transport: HttpTransport, request: SourceHealthApiV1NewsSourcesSourceIdHealthGetRequest) -> SourceHealthApiV1NewsSourcesSourceIdHealthGetSuccess:
    return await transport.invoke(SOURCEHEALTHAPIV1NEWSSOURCESSOURCEIDHEALTHGET_OPERATION, path_parameters={'source_id': str(request.source_id)}, query_parameters={}, body=None)

class SourceSnapshotsApiV1NewsSourcesSourceIdSnapshotsGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    source_id: int

class SourceSnapshotsApiV1NewsSourcesSourceIdSnapshotsGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

SourceSnapshotsApiV1NewsSourcesSourceIdSnapshotsGetError = SafeTransportError

SOURCESNAPSHOTSAPIV1NEWSSOURCESSOURCEIDSNAPSHOTSGET_SECURITY = SecurityMetadata(
    identity='public:source_snapshots_api_v1_news_sources__source_id__snapshots_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='source_snapshots_api_v1_news_sources__source_id__snapshots_get', review_owner='Stage 1B0-R7',
)
SOURCESNAPSHOTSAPIV1NEWSSOURCESSOURCEIDSNAPSHOTSGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0193', operation_id='source_snapshots_api_v1_news_sources__source_id__snapshots_get',
    method='GET', path='/api/v1/news/sources/{source_id}/snapshots', backend_tag='market-intelligence',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=SourceSnapshotsApiV1NewsSourcesSourceIdSnapshotsGetSuccess, security=SOURCESNAPSHOTSAPIV1NEWSSOURCESSOURCEIDSNAPSHOTSGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:source_snapshots_api_v1_news_sources__source_id__snapshots_get',
    response_media_type='application/json',
)
async def source_snapshots_api_v1_news_sources__source_id__snapshots_get(transport: HttpTransport, request: SourceSnapshotsApiV1NewsSourcesSourceIdSnapshotsGetRequest) -> SourceSnapshotsApiV1NewsSourcesSourceIdSnapshotsGetSuccess:
    return await transport.invoke(SOURCESNAPSHOTSAPIV1NEWSSOURCESSOURCEIDSNAPSHOTSGET_OPERATION, path_parameters={'source_id': str(request.source_id)}, query_parameters={}, body=None)

class GetArticleExplanationApiV1NewsArticleIdExplanationGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    article_id: int

class GetArticleExplanationApiV1NewsArticleIdExplanationGetSuccess(RootModel[ResponseEnvelopeDictStrObject]):
    pass

GetArticleExplanationApiV1NewsArticleIdExplanationGetError = SafeTransportError

GETARTICLEEXPLANATIONAPIV1NEWSARTICLEIDEXPLANATIONGET_SECURITY = SecurityMetadata(
    identity='public:get_article_explanation_api_v1_news__article_id__explanation_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_article_explanation_api_v1_news__article_id__explanation_get', review_owner='Stage 1B0-R7',
)
GETARTICLEEXPLANATIONAPIV1NEWSARTICLEIDEXPLANATIONGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0194', operation_id='get_article_explanation_api_v1_news__article_id__explanation_get',
    method='GET', path='/api/v1/news/{article_id}/explanation', backend_tag='news',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetArticleExplanationApiV1NewsArticleIdExplanationGetSuccess, security=GETARTICLEEXPLANATIONAPIV1NEWSARTICLEIDEXPLANATIONGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_article_explanation_api_v1_news__article_id__explanation_get',
    response_media_type='application/json',
)
async def get_article_explanation_api_v1_news__article_id__explanation_get(transport: HttpTransport, request: GetArticleExplanationApiV1NewsArticleIdExplanationGetRequest) -> GetArticleExplanationApiV1NewsArticleIdExplanationGetSuccess:
    return await transport.invoke(GETARTICLEEXPLANATIONAPIV1NEWSARTICLEIDEXPLANATIONGET_OPERATION, path_parameters={'article_id': str(request.article_id)}, query_parameters={}, body=None)

class GetArticleImpactApiV1NewsArticleIdImpactGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    article_id: int

class GetArticleImpactApiV1NewsArticleIdImpactGetSuccess(RootModel[ResponseEnvelopeDictStrObject]):
    pass

GetArticleImpactApiV1NewsArticleIdImpactGetError = SafeTransportError

GETARTICLEIMPACTAPIV1NEWSARTICLEIDIMPACTGET_SECURITY = SecurityMetadata(
    identity='public:get_article_impact_api_v1_news__article_id__impact_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_article_impact_api_v1_news__article_id__impact_get', review_owner='Stage 1B0-R7',
)
GETARTICLEIMPACTAPIV1NEWSARTICLEIDIMPACTGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0195', operation_id='get_article_impact_api_v1_news__article_id__impact_get',
    method='GET', path='/api/v1/news/{article_id}/impact', backend_tag='news',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetArticleImpactApiV1NewsArticleIdImpactGetSuccess, security=GETARTICLEIMPACTAPIV1NEWSARTICLEIDIMPACTGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_article_impact_api_v1_news__article_id__impact_get',
    response_media_type='application/json',
)
async def get_article_impact_api_v1_news__article_id__impact_get(transport: HttpTransport, request: GetArticleImpactApiV1NewsArticleIdImpactGetRequest) -> GetArticleImpactApiV1NewsArticleIdImpactGetSuccess:
    return await transport.invoke(GETARTICLEIMPACTAPIV1NEWSARTICLEIDIMPACTGET_OPERATION, path_parameters={'article_id': str(request.article_id)}, query_parameters={}, body=None)

class GetArticleNarrativesApiV1NewsArticleIdNarrativesGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    article_id: int

class GetArticleNarrativesApiV1NewsArticleIdNarrativesGetSuccess(RootModel[ResponseEnvelopeListDictStrObject]):
    pass

GetArticleNarrativesApiV1NewsArticleIdNarrativesGetError = SafeTransportError

GETARTICLENARRATIVESAPIV1NEWSARTICLEIDNARRATIVESGET_SECURITY = SecurityMetadata(
    identity='public:get_article_narratives_api_v1_news__article_id__narratives_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_article_narratives_api_v1_news__article_id__narratives_get', review_owner='Stage 1B0-R7',
)
GETARTICLENARRATIVESAPIV1NEWSARTICLEIDNARRATIVESGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0196', operation_id='get_article_narratives_api_v1_news__article_id__narratives_get',
    method='GET', path='/api/v1/news/{article_id}/narratives', backend_tag='news',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetArticleNarrativesApiV1NewsArticleIdNarrativesGetSuccess, security=GETARTICLENARRATIVESAPIV1NEWSARTICLEIDNARRATIVESGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_article_narratives_api_v1_news__article_id__narratives_get',
    response_media_type='application/json',
)
async def get_article_narratives_api_v1_news__article_id__narratives_get(transport: HttpTransport, request: GetArticleNarrativesApiV1NewsArticleIdNarrativesGetRequest) -> GetArticleNarrativesApiV1NewsArticleIdNarrativesGetSuccess:
    return await transport.invoke(GETARTICLENARRATIVESAPIV1NEWSARTICLEIDNARRATIVESGET_OPERATION, path_parameters={'article_id': str(request.article_id)}, query_parameters={}, body=None)

class GetArticleScoreApiV1NewsArticleIdScoreGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    article_id: int

class GetArticleScoreApiV1NewsArticleIdScoreGetSuccess(RootModel[ResponseEnvelopeDictStrObject]):
    pass

GetArticleScoreApiV1NewsArticleIdScoreGetError = SafeTransportError

GETARTICLESCOREAPIV1NEWSARTICLEIDSCOREGET_SECURITY = SecurityMetadata(
    identity='public:get_article_score_api_v1_news__article_id__score_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_article_score_api_v1_news__article_id__score_get', review_owner='Stage 1B0-R7',
)
GETARTICLESCOREAPIV1NEWSARTICLEIDSCOREGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0197', operation_id='get_article_score_api_v1_news__article_id__score_get',
    method='GET', path='/api/v1/news/{article_id}/score', backend_tag='news',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetArticleScoreApiV1NewsArticleIdScoreGetSuccess, security=GETARTICLESCOREAPIV1NEWSARTICLEIDSCOREGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_article_score_api_v1_news__article_id__score_get',
    response_media_type='application/json',
)
async def get_article_score_api_v1_news__article_id__score_get(transport: HttpTransport, request: GetArticleScoreApiV1NewsArticleIdScoreGetRequest) -> GetArticleScoreApiV1NewsArticleIdScoreGetSuccess:
    return await transport.invoke(GETARTICLESCOREAPIV1NEWSARTICLEIDSCOREGET_OPERATION, path_parameters={'article_id': str(request.article_id)}, query_parameters={}, body=None)

class GetArticleScoresApiV1NewsArticleIdScoresGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    article_id: int

class GetArticleScoresApiV1NewsArticleIdScoresGetSuccess(RootModel[ResponseEnvelopeDictStrObject]):
    pass

GetArticleScoresApiV1NewsArticleIdScoresGetError = SafeTransportError

GETARTICLESCORESAPIV1NEWSARTICLEIDSCORESGET_SECURITY = SecurityMetadata(
    identity='public:get_article_scores_api_v1_news__article_id__scores_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_article_scores_api_v1_news__article_id__scores_get', review_owner='Stage 1B0-R7',
)
GETARTICLESCORESAPIV1NEWSARTICLEIDSCORESGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0198', operation_id='get_article_scores_api_v1_news__article_id__scores_get',
    method='GET', path='/api/v1/news/{article_id}/scores', backend_tag='news',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetArticleScoresApiV1NewsArticleIdScoresGetSuccess, security=GETARTICLESCORESAPIV1NEWSARTICLEIDSCORESGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_article_scores_api_v1_news__article_id__scores_get',
    response_media_type='application/json',
)
async def get_article_scores_api_v1_news__article_id__scores_get(transport: HttpTransport, request: GetArticleScoresApiV1NewsArticleIdScoresGetRequest) -> GetArticleScoresApiV1NewsArticleIdScoresGetSuccess:
    return await transport.invoke(GETARTICLESCORESAPIV1NEWSARTICLEIDSCORESGET_OPERATION, path_parameters={'article_id': str(request.article_id)}, query_parameters={}, body=None)

class OnchainEventsApiV1OnchainEventsGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    limit: int | None = None
    offset: int | None = None

class OnchainEventsApiV1OnchainEventsGetSuccess(RootModel[ResponseEnvelopePaginatedDataOnchainEventOut]):
    pass

OnchainEventsApiV1OnchainEventsGetError = SafeTransportError

ONCHAINEVENTSAPIV1ONCHAINEVENTSGET_SECURITY = SecurityMetadata(
    identity='public:onchain_events_api_v1_onchain_events_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='onchain_events_api_v1_onchain_events_get', review_owner='Stage 1B0-R7',
)
ONCHAINEVENTSAPIV1ONCHAINEVENTSGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0200', operation_id='onchain_events_api_v1_onchain_events_get',
    method='GET', path='/api/v1/onchain/events', backend_tag='onchain',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=OnchainEventsApiV1OnchainEventsGetSuccess, security=ONCHAINEVENTSAPIV1ONCHAINEVENTSGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:onchain_events_api_v1_onchain_events_get',
    response_media_type='application/json',
)
async def onchain_events_api_v1_onchain_events_get(transport: HttpTransport, request: OnchainEventsApiV1OnchainEventsGetRequest) -> OnchainEventsApiV1OnchainEventsGetSuccess:
    return await transport.invoke(ONCHAINEVENTSAPIV1ONCHAINEVENTSGET_OPERATION, path_parameters={}, query_parameters={'limit': serialize_query_value(request.limit), 'offset': serialize_query_value(request.offset)}, body=None)

class OnchainStateApiV1OnchainStateGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    tip_height: int | None | None = None
    observed_block_height: int | None | None = None
    headers_height: int | None | None = None
    provider_probe: bool | None = None

class OnchainStateApiV1OnchainStateGetSuccess(RootModel[ResponseEnvelopeOnchainChainStateOut]):
    pass

OnchainStateApiV1OnchainStateGetError = SafeTransportError

ONCHAINSTATEAPIV1ONCHAINSTATEGET_SECURITY = SecurityMetadata(
    identity='public:onchain_state_api_v1_onchain_state_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='onchain_state_api_v1_onchain_state_get', review_owner='Stage 1B0-R7',
)
ONCHAINSTATEAPIV1ONCHAINSTATEGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0201', operation_id='onchain_state_api_v1_onchain_state_get',
    method='GET', path='/api/v1/onchain/state', backend_tag='onchain',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=OnchainStateApiV1OnchainStateGetSuccess, security=ONCHAINSTATEAPIV1ONCHAINSTATEGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:onchain_state_api_v1_onchain_state_get',
    response_media_type='application/json',
)
async def onchain_state_api_v1_onchain_state_get(transport: HttpTransport, request: OnchainStateApiV1OnchainStateGetRequest) -> OnchainStateApiV1OnchainStateGetSuccess:
    return await transport.invoke(ONCHAINSTATEAPIV1ONCHAINSTATEGET_OPERATION, path_parameters={}, query_parameters={'tip_height': serialize_query_value(request.tip_height), 'observed_block_height': serialize_query_value(request.observed_block_height), 'headers_height': serialize_query_value(request.headers_height), 'provider_probe': serialize_query_value(request.provider_probe)}, body=None)

class PublicFeaturesApiV1PublicFeaturesGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    pass

class PublicFeaturesApiV1PublicFeaturesGetSuccess(RootModel[ResponseEnvelopeListPublicFeatureEntry]):
    pass

PublicFeaturesApiV1PublicFeaturesGetError = SafeTransportError

PUBLICFEATURESAPIV1PUBLICFEATURESGET_SECURITY = SecurityMetadata(
    identity='public:public_features_api_v1_public_features_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='public_features_api_v1_public_features_get', review_owner='Stage 1B0-R7',
)
PUBLICFEATURESAPIV1PUBLICFEATURESGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0246', operation_id='public_features_api_v1_public_features_get',
    method='GET', path='/api/v1/public/features', backend_tag='public',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=PublicFeaturesApiV1PublicFeaturesGetSuccess, security=PUBLICFEATURESAPIV1PUBLICFEATURESGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:public_features_api_v1_public_features_get',
    response_media_type='application/json',
)
async def public_features_api_v1_public_features_get(transport: HttpTransport, request: PublicFeaturesApiV1PublicFeaturesGetRequest) -> PublicFeaturesApiV1PublicFeaturesGetSuccess:
    return await transport.invoke(PUBLICFEATURESAPIV1PUBLICFEATURESGET_OPERATION, path_parameters={}, query_parameters={}, body=None)

class PublicLandingApiV1PublicLandingGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    pass

class PublicLandingApiV1PublicLandingGetSuccess(RootModel[ResponseEnvelopePublicLandingResponse]):
    pass

PublicLandingApiV1PublicLandingGetError = SafeTransportError

PUBLICLANDINGAPIV1PUBLICLANDINGGET_SECURITY = SecurityMetadata(
    identity='public:public_landing_api_v1_public_landing_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='public_landing_api_v1_public_landing_get', review_owner='Stage 1B0-R7',
)
PUBLICLANDINGAPIV1PUBLICLANDINGGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0247', operation_id='public_landing_api_v1_public_landing_get',
    method='GET', path='/api/v1/public/landing', backend_tag='public',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=PublicLandingApiV1PublicLandingGetSuccess, security=PUBLICLANDINGAPIV1PUBLICLANDINGGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:public_landing_api_v1_public_landing_get',
    response_media_type='application/json',
)
async def public_landing_api_v1_public_landing_get(transport: HttpTransport, request: PublicLandingApiV1PublicLandingGetRequest) -> PublicLandingApiV1PublicLandingGetSuccess:
    return await transport.invoke(PUBLICLANDINGAPIV1PUBLICLANDINGGET_OPERATION, path_parameters={}, query_parameters={}, body=None)

class PublicRoadmapApiV1PublicRoadmapGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    pass

class PublicRoadmapApiV1PublicRoadmapGetSuccess(RootModel[ResponseEnvelopePublicRoadmapResponse]):
    pass

PublicRoadmapApiV1PublicRoadmapGetError = SafeTransportError

PUBLICROADMAPAPIV1PUBLICROADMAPGET_SECURITY = SecurityMetadata(
    identity='public:public_roadmap_api_v1_public_roadmap_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='public_roadmap_api_v1_public_roadmap_get', review_owner='Stage 1B0-R7',
)
PUBLICROADMAPAPIV1PUBLICROADMAPGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0248', operation_id='public_roadmap_api_v1_public_roadmap_get',
    method='GET', path='/api/v1/public/roadmap', backend_tag='public',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=PublicRoadmapApiV1PublicRoadmapGetSuccess, security=PUBLICROADMAPAPIV1PUBLICROADMAPGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:public_roadmap_api_v1_public_roadmap_get',
    response_media_type='application/json',
)
async def public_roadmap_api_v1_public_roadmap_get(transport: HttpTransport, request: PublicRoadmapApiV1PublicRoadmapGetRequest) -> PublicRoadmapApiV1PublicRoadmapGetSuccess:
    return await transport.invoke(PUBLICROADMAPAPIV1PUBLICROADMAPGET_OPERATION, path_parameters={}, query_parameters={}, body=None)

class PublicStatsApiV1PublicStatsGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    pass

class PublicStatsApiV1PublicStatsGetSuccess(RootModel[ResponseEnvelopePublicStatsResponse]):
    pass

PublicStatsApiV1PublicStatsGetError = SafeTransportError

PUBLICSTATSAPIV1PUBLICSTATSGET_SECURITY = SecurityMetadata(
    identity='public:public_stats_api_v1_public_stats_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='public_stats_api_v1_public_stats_get', review_owner='Stage 1B0-R7',
)
PUBLICSTATSAPIV1PUBLICSTATSGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0249', operation_id='public_stats_api_v1_public_stats_get',
    method='GET', path='/api/v1/public/stats', backend_tag='public',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=PublicStatsApiV1PublicStatsGetSuccess, security=PUBLICSTATSAPIV1PUBLICSTATSGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:public_stats_api_v1_public_stats_get',
    response_media_type='application/json',
)
async def public_stats_api_v1_public_stats_get(transport: HttpTransport, request: PublicStatsApiV1PublicStatsGetRequest) -> PublicStatsApiV1PublicStatsGetSuccess:
    return await transport.invoke(PUBLICSTATSAPIV1PUBLICSTATSGET_OPERATION, path_parameters={}, query_parameters={}, body=None)

class PublicStatusApiV1PublicStatusGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    pass

class PublicStatusApiV1PublicStatusGetSuccess(RootModel[ResponseEnvelopePublicStatusResponse]):
    pass

PublicStatusApiV1PublicStatusGetError = SafeTransportError

PUBLICSTATUSAPIV1PUBLICSTATUSGET_SECURITY = SecurityMetadata(
    identity='public:public_status_api_v1_public_status_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='public_status_api_v1_public_status_get', review_owner='Stage 1B0-R7',
)
PUBLICSTATUSAPIV1PUBLICSTATUSGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0250', operation_id='public_status_api_v1_public_status_get',
    method='GET', path='/api/v1/public/status', backend_tag='public',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=PublicStatusApiV1PublicStatusGetSuccess, security=PUBLICSTATUSAPIV1PUBLICSTATUSGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:public_status_api_v1_public_status_get',
    response_media_type='application/json',
)
async def public_status_api_v1_public_status_get(transport: HttpTransport, request: PublicStatusApiV1PublicStatusGetRequest) -> PublicStatusApiV1PublicStatusGetSuccess:
    return await transport.invoke(PUBLICSTATUSAPIV1PUBLICSTATUSGET_OPERATION, path_parameters={}, query_parameters={}, body=None)

class PublicTraceSummaryApiV1PublicTraceReportIdSummaryGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    report_id: int

class PublicTraceSummaryApiV1PublicTraceReportIdSummaryGetSuccess(RootModel[ResponseEnvelopePublicTraceSummary]):
    pass

PublicTraceSummaryApiV1PublicTraceReportIdSummaryGetError = SafeTransportError

PUBLICTRACESUMMARYAPIV1PUBLICTRACEREPORTIDSUMMARYGET_SECURITY = SecurityMetadata(
    identity='public:public_trace_summary_api_v1_public_trace__report_id__summary_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='public_trace_summary_api_v1_public_trace__report_id__summary_get', review_owner='Stage 1B0-R7',
)
PUBLICTRACESUMMARYAPIV1PUBLICTRACEREPORTIDSUMMARYGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0251', operation_id='public_trace_summary_api_v1_public_trace__report_id__summary_get',
    method='GET', path='/api/v1/public/trace/{report_id}/summary', backend_tag='public',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=PublicTraceSummaryApiV1PublicTraceReportIdSummaryGetSuccess, security=PUBLICTRACESUMMARYAPIV1PUBLICTRACEREPORTIDSUMMARYGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:public_trace_summary_api_v1_public_trace__report_id__summary_get',
    response_media_type='application/json',
)
async def public_trace_summary_api_v1_public_trace__report_id__summary_get(transport: HttpTransport, request: PublicTraceSummaryApiV1PublicTraceReportIdSummaryGetRequest) -> PublicTraceSummaryApiV1PublicTraceReportIdSummaryGetSuccess:
    return await transport.invoke(PUBLICTRACESUMMARYAPIV1PUBLICTRACEREPORTIDSUMMARYGET_OPERATION, path_parameters={'report_id': str(request.report_id)}, query_parameters={}, body=None)

class LatestSignalsApiV1SignalsLatestGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    pass

class LatestSignalsApiV1SignalsLatestGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

LatestSignalsApiV1SignalsLatestGetError = SafeTransportError

LATESTSIGNALSAPIV1SIGNALSLATESTGET_SECURITY = SecurityMetadata(
    identity='public:latest_signals_api_v1_signals_latest_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='latest_signals_api_v1_signals_latest_get', review_owner='Stage 1B0-R7',
)
LATESTSIGNALSAPIV1SIGNALSLATESTGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0252', operation_id='latest_signals_api_v1_signals_latest_get',
    method='GET', path='/api/v1/signals/latest', backend_tag='intelligence-signals',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=LatestSignalsApiV1SignalsLatestGetSuccess, security=LATESTSIGNALSAPIV1SIGNALSLATESTGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:latest_signals_api_v1_signals_latest_get',
    response_media_type='application/json',
)
async def latest_signals_api_v1_signals_latest_get(transport: HttpTransport, request: LatestSignalsApiV1SignalsLatestGetRequest) -> LatestSignalsApiV1SignalsLatestGetSuccess:
    return await transport.invoke(LATESTSIGNALSAPIV1SIGNALSLATESTGET_OPERATION, path_parameters={}, query_parameters={}, body=None)

class NewsMarketImpactSignalsApiV1SignalsNewsMarketImpactGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    pass

class NewsMarketImpactSignalsApiV1SignalsNewsMarketImpactGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

NewsMarketImpactSignalsApiV1SignalsNewsMarketImpactGetError = SafeTransportError

NEWSMARKETIMPACTSIGNALSAPIV1SIGNALSNEWSMARKETIMPACTGET_SECURITY = SecurityMetadata(
    identity='public:news_market_impact_signals_api_v1_signals_news_market_impact_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='news_market_impact_signals_api_v1_signals_news_market_impact_get', review_owner='Stage 1B0-R7',
)
NEWSMARKETIMPACTSIGNALSAPIV1SIGNALSNEWSMARKETIMPACTGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0253', operation_id='news_market_impact_signals_api_v1_signals_news_market_impact_get',
    method='GET', path='/api/v1/signals/news-market-impact', backend_tag='intelligence-signals',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=NewsMarketImpactSignalsApiV1SignalsNewsMarketImpactGetSuccess, security=NEWSMARKETIMPACTSIGNALSAPIV1SIGNALSNEWSMARKETIMPACTGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:news_market_impact_signals_api_v1_signals_news_market_impact_get',
    response_media_type='application/json',
)
async def news_market_impact_signals_api_v1_signals_news_market_impact_get(transport: HttpTransport, request: NewsMarketImpactSignalsApiV1SignalsNewsMarketImpactGetRequest) -> NewsMarketImpactSignalsApiV1SignalsNewsMarketImpactGetSuccess:
    return await transport.invoke(NEWSMARKETIMPACTSIGNALSAPIV1SIGNALSNEWSMARKETIMPACTGET_OPERATION, path_parameters={}, query_parameters={}, body=None)

class TopSignalsApiV1SignalsTopGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    limit: int | None = None
    offset: int | None = None
    horizon: str | None | None = None

class TopSignalsApiV1SignalsTopGetSuccess(RootModel[ResponseEnvelopePaginatedDataSignalOut]):
    pass

TopSignalsApiV1SignalsTopGetError = SafeTransportError

TOPSIGNALSAPIV1SIGNALSTOPGET_SECURITY = SecurityMetadata(
    identity='public:top_signals_api_v1_signals_top_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='top_signals_api_v1_signals_top_get', review_owner='Stage 1B0-R7',
)
TOPSIGNALSAPIV1SIGNALSTOPGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0254', operation_id='top_signals_api_v1_signals_top_get',
    method='GET', path='/api/v1/signals/top', backend_tag='signals',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=TopSignalsApiV1SignalsTopGetSuccess, security=TOPSIGNALSAPIV1SIGNALSTOPGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:top_signals_api_v1_signals_top_get',
    response_media_type='application/json',
)
async def top_signals_api_v1_signals_top_get(transport: HttpTransport, request: TopSignalsApiV1SignalsTopGetRequest) -> TopSignalsApiV1SignalsTopGetSuccess:
    return await transport.invoke(TOPSIGNALSAPIV1SIGNALSTOPGET_OPERATION, path_parameters={}, query_parameters={'limit': serialize_query_value(request.limit), 'offset': serialize_query_value(request.offset), 'horizon': serialize_query_value(request.horizon)}, body=None)

class GetSignalApiV1SignalsSignalIdGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    signal_id: int

class GetSignalApiV1SignalsSignalIdGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

GetSignalApiV1SignalsSignalIdGetError = SafeTransportError

GETSIGNALAPIV1SIGNALSSIGNALIDGET_SECURITY = SecurityMetadata(
    identity='public:get_signal_api_v1_signals__signal_id__get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_signal_api_v1_signals__signal_id__get', review_owner='Stage 1B0-R7',
)
GETSIGNALAPIV1SIGNALSSIGNALIDGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0255', operation_id='get_signal_api_v1_signals__signal_id__get',
    method='GET', path='/api/v1/signals/{signal_id}', backend_tag='intelligence-signals',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetSignalApiV1SignalsSignalIdGetSuccess, security=GETSIGNALAPIV1SIGNALSSIGNALIDGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_signal_api_v1_signals__signal_id__get',
    response_media_type='application/json',
)
async def get_signal_api_v1_signals__signal_id__get(transport: HttpTransport, request: GetSignalApiV1SignalsSignalIdGetRequest) -> GetSignalApiV1SignalsSignalIdGetSuccess:
    return await transport.invoke(GETSIGNALAPIV1SIGNALSSIGNALIDGET_OPERATION, path_parameters={'signal_id': str(request.signal_id)}, query_parameters={}, body=None)

class GetSignalDeliveryLogsApiV1SignalsSignalIdDeliveryLogsGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    signal_id: int

class GetSignalDeliveryLogsApiV1SignalsSignalIdDeliveryLogsGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

GetSignalDeliveryLogsApiV1SignalsSignalIdDeliveryLogsGetError = SafeTransportError

GETSIGNALDELIVERYLOGSAPIV1SIGNALSSIGNALIDDELIVERYLOGSGET_SECURITY = SecurityMetadata(
    identity='public:get_signal_delivery_logs_api_v1_signals__signal_id__delivery_logs_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_signal_delivery_logs_api_v1_signals__signal_id__delivery_logs_get', review_owner='Stage 1B0-R7',
)
GETSIGNALDELIVERYLOGSAPIV1SIGNALSSIGNALIDDELIVERYLOGSGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0256', operation_id='get_signal_delivery_logs_api_v1_signals__signal_id__delivery_logs_get',
    method='GET', path='/api/v1/signals/{signal_id}/delivery-logs', backend_tag='intelligence-signals',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetSignalDeliveryLogsApiV1SignalsSignalIdDeliveryLogsGetSuccess, security=GETSIGNALDELIVERYLOGSAPIV1SIGNALSSIGNALIDDELIVERYLOGSGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_signal_delivery_logs_api_v1_signals__signal_id__delivery_logs_get',
    response_media_type='application/json',
)
async def get_signal_delivery_logs_api_v1_signals__signal_id__delivery_logs_get(transport: HttpTransport, request: GetSignalDeliveryLogsApiV1SignalsSignalIdDeliveryLogsGetRequest) -> GetSignalDeliveryLogsApiV1SignalsSignalIdDeliveryLogsGetSuccess:
    return await transport.invoke(GETSIGNALDELIVERYLOGSAPIV1SIGNALSSIGNALIDDELIVERYLOGSGET_OPERATION, path_parameters={'signal_id': str(request.signal_id)}, query_parameters={}, body=None)

class GetSignalEvidenceApiV1SignalsSignalIdEvidenceGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    signal_id: int

class GetSignalEvidenceApiV1SignalsSignalIdEvidenceGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

GetSignalEvidenceApiV1SignalsSignalIdEvidenceGetError = SafeTransportError

GETSIGNALEVIDENCEAPIV1SIGNALSSIGNALIDEVIDENCEGET_SECURITY = SecurityMetadata(
    identity='public:get_signal_evidence_api_v1_signals__signal_id__evidence_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_signal_evidence_api_v1_signals__signal_id__evidence_get', review_owner='Stage 1B0-R7',
)
GETSIGNALEVIDENCEAPIV1SIGNALSSIGNALIDEVIDENCEGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0257', operation_id='get_signal_evidence_api_v1_signals__signal_id__evidence_get',
    method='GET', path='/api/v1/signals/{signal_id}/evidence', backend_tag='intelligence-signals',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetSignalEvidenceApiV1SignalsSignalIdEvidenceGetSuccess, security=GETSIGNALEVIDENCEAPIV1SIGNALSSIGNALIDEVIDENCEGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_signal_evidence_api_v1_signals__signal_id__evidence_get',
    response_media_type='application/json',
)
async def get_signal_evidence_api_v1_signals__signal_id__evidence_get(transport: HttpTransport, request: GetSignalEvidenceApiV1SignalsSignalIdEvidenceGetRequest) -> GetSignalEvidenceApiV1SignalsSignalIdEvidenceGetSuccess:
    return await transport.invoke(GETSIGNALEVIDENCEAPIV1SIGNALSSIGNALIDEVIDENCEGET_OPERATION, path_parameters={'signal_id': str(request.signal_id)}, query_parameters={}, body=None)

class SignalExplanationApiV1SignalsSignalIdExplanationGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    signal_id: int

class SignalExplanationApiV1SignalsSignalIdExplanationGetSuccess(RootModel[ResponseEnvelopeSignalExplanationOut]):
    pass

SignalExplanationApiV1SignalsSignalIdExplanationGetError = SafeTransportError

SIGNALEXPLANATIONAPIV1SIGNALSSIGNALIDEXPLANATIONGET_SECURITY = SecurityMetadata(
    identity='public:signal_explanation_api_v1_signals__signal_id__explanation_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='signal_explanation_api_v1_signals__signal_id__explanation_get', review_owner='Stage 1B0-R7',
)
SIGNALEXPLANATIONAPIV1SIGNALSSIGNALIDEXPLANATIONGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0258', operation_id='signal_explanation_api_v1_signals__signal_id__explanation_get',
    method='GET', path='/api/v1/signals/{signal_id}/explanation', backend_tag='signals',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=SignalExplanationApiV1SignalsSignalIdExplanationGetSuccess, security=SIGNALEXPLANATIONAPIV1SIGNALSSIGNALIDEXPLANATIONGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:signal_explanation_api_v1_signals__signal_id__explanation_get',
    response_media_type='application/json',
)
async def signal_explanation_api_v1_signals__signal_id__explanation_get(transport: HttpTransport, request: SignalExplanationApiV1SignalsSignalIdExplanationGetRequest) -> SignalExplanationApiV1SignalsSignalIdExplanationGetSuccess:
    return await transport.invoke(SIGNALEXPLANATIONAPIV1SIGNALSSIGNALIDEXPLANATIONGET_OPERATION, path_parameters={'signal_id': str(request.signal_id)}, query_parameters={}, body=None)

class SignalRecommendationsApiV1SignalsSignalIdRecommendationsGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    signal_id: int

class SignalRecommendationsApiV1SignalsSignalIdRecommendationsGetSuccess(RootModel[ResponseEnvelopeSignalRecommendationOut]):
    pass

SignalRecommendationsApiV1SignalsSignalIdRecommendationsGetError = SafeTransportError

SIGNALRECOMMENDATIONSAPIV1SIGNALSSIGNALIDRECOMMENDATIONSGET_SECURITY = SecurityMetadata(
    identity='public:signal_recommendations_api_v1_signals__signal_id__recommendations_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='signal_recommendations_api_v1_signals__signal_id__recommendations_get', review_owner='Stage 1B0-R7',
)
SIGNALRECOMMENDATIONSAPIV1SIGNALSSIGNALIDRECOMMENDATIONSGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0259', operation_id='signal_recommendations_api_v1_signals__signal_id__recommendations_get',
    method='GET', path='/api/v1/signals/{signal_id}/recommendations', backend_tag='signals',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=SignalRecommendationsApiV1SignalsSignalIdRecommendationsGetSuccess, security=SIGNALRECOMMENDATIONSAPIV1SIGNALSSIGNALIDRECOMMENDATIONSGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:signal_recommendations_api_v1_signals__signal_id__recommendations_get',
    response_media_type='application/json',
)
async def signal_recommendations_api_v1_signals__signal_id__recommendations_get(transport: HttpTransport, request: SignalRecommendationsApiV1SignalsSignalIdRecommendationsGetRequest) -> SignalRecommendationsApiV1SignalsSignalIdRecommendationsGetSuccess:
    return await transport.invoke(SIGNALRECOMMENDATIONSAPIV1SIGNALSSIGNALIDRECOMMENDATIONSGET_OPERATION, path_parameters={'signal_id': str(request.signal_id)}, query_parameters={}, body=None)

class StorageStatusApiV1StorageStatusGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    pass

class StorageStatusApiV1StorageStatusGetSuccess(RootModel[StorageStatusResponse]):
    pass

StorageStatusApiV1StorageStatusGetError = SafeTransportError

STORAGESTATUSAPIV1STORAGESTATUSGET_SECURITY = SecurityMetadata(
    identity='public:storage_status_api_v1_storage_status_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='storage_status_api_v1_storage_status_get', review_owner='Stage 1B0-R7',
)
STORAGESTATUSAPIV1STORAGESTATUSGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0260', operation_id='storage_status_api_v1_storage_status_get',
    method='GET', path='/api/v1/storage/status', backend_tag='storage',
    product='Operator Console', disposition='UI_REQUIRED',
    success_status=200, response_type=StorageStatusApiV1StorageStatusGetSuccess, security=STORAGESTATUSAPIV1STORAGESTATUSGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:storage_status_api_v1_storage_status_get',
    response_media_type='application/json',
)
async def storage_status_api_v1_storage_status_get(transport: HttpTransport, request: StorageStatusApiV1StorageStatusGetRequest) -> StorageStatusApiV1StorageStatusGetSuccess:
    return await transport.invoke(STORAGESTATUSAPIV1STORAGESTATUSGET_OPERATION, path_parameters={}, query_parameters={}, body=None)

class TimescaleOperationsStatusApiV1StorageTimescaleStatusGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    pass

class TimescaleOperationsStatusApiV1StorageTimescaleStatusGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

TimescaleOperationsStatusApiV1StorageTimescaleStatusGetError = SafeTransportError

TIMESCALEOPERATIONSSTATUSAPIV1STORAGETIMESCALESTATUSGET_SECURITY = SecurityMetadata(
    identity='public:timescale_operations_status_api_v1_storage_timescale_status_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='timescale_operations_status_api_v1_storage_timescale_status_get', review_owner='Stage 1B0-R7',
)
TIMESCALEOPERATIONSSTATUSAPIV1STORAGETIMESCALESTATUSGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0261', operation_id='timescale_operations_status_api_v1_storage_timescale_status_get',
    method='GET', path='/api/v1/storage/timescale/status', backend_tag='storage',
    product='Operator Console', disposition='UI_REQUIRED',
    success_status=200, response_type=TimescaleOperationsStatusApiV1StorageTimescaleStatusGetSuccess, security=TIMESCALEOPERATIONSSTATUSAPIV1STORAGETIMESCALESTATUSGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:timescale_operations_status_api_v1_storage_timescale_status_get',
    response_media_type='application/json',
)
async def timescale_operations_status_api_v1_storage_timescale_status_get(transport: HttpTransport, request: TimescaleOperationsStatusApiV1StorageTimescaleStatusGetRequest) -> TimescaleOperationsStatusApiV1StorageTimescaleStatusGetSuccess:
    return await transport.invoke(TIMESCALEOPERATIONSSTATUSAPIV1STORAGETIMESCALESTATUSGET_OPERATION, path_parameters={}, query_parameters={}, body=None)

class AnalyzeAddressApiV1TraceAddressAddressGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    address: str

class AnalyzeAddressApiV1TraceAddressAddressGetSuccess(RootModel[ResponseEnvelopeTraceReport]):
    pass

AnalyzeAddressApiV1TraceAddressAddressGetError = SafeTransportError

ANALYZEADDRESSAPIV1TRACEADDRESSADDRESSGET_SECURITY = SecurityMetadata(
    identity='public:analyze_address_api_v1_trace_address__address__get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='analyze_address_api_v1_trace_address__address__get', review_owner='Stage 1B0-R7',
)
ANALYZEADDRESSAPIV1TRACEADDRESSADDRESSGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0262', operation_id='analyze_address_api_v1_trace_address__address__get',
    method='GET', path='/api/v1/trace/address/{address}', backend_tag='trace',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=AnalyzeAddressApiV1TraceAddressAddressGetSuccess, security=ANALYZEADDRESSAPIV1TRACEADDRESSADDRESSGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:analyze_address_api_v1_trace_address__address__get',
    response_media_type='application/json',
)
async def analyze_address_api_v1_trace_address__address__get(transport: HttpTransport, request: AnalyzeAddressApiV1TraceAddressAddressGetRequest) -> AnalyzeAddressApiV1TraceAddressAddressGetSuccess:
    return await transport.invoke(ANALYZEADDRESSAPIV1TRACEADDRESSADDRESSGET_OPERATION, path_parameters={'address': str(request.address)}, query_parameters={}, body=None)

class TraceAlertsApiV1TraceAlertsGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    pass

class TraceAlertsApiV1TraceAlertsGetSuccess(RootModel[ResponseEnvelopeListDictStrObject]):
    pass

TraceAlertsApiV1TraceAlertsGetError = SafeTransportError

TRACEALERTSAPIV1TRACEALERTSGET_SECURITY = SecurityMetadata(
    identity='public:trace_alerts_api_v1_trace_alerts_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='trace_alerts_api_v1_trace_alerts_get', review_owner='Stage 1B0-R7',
)
TRACEALERTSAPIV1TRACEALERTSGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0263', operation_id='trace_alerts_api_v1_trace_alerts_get',
    method='GET', path='/api/v1/trace/alerts', backend_tag='trace',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=TraceAlertsApiV1TraceAlertsGetSuccess, security=TRACEALERTSAPIV1TRACEALERTSGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:trace_alerts_api_v1_trace_alerts_get',
    response_media_type='application/json',
)
async def trace_alerts_api_v1_trace_alerts_get(transport: HttpTransport, request: TraceAlertsApiV1TraceAlertsGetRequest) -> TraceAlertsApiV1TraceAlertsGetSuccess:
    return await transport.invoke(TRACEALERTSAPIV1TRACEALERTSGET_OPERATION, path_parameters={}, query_parameters={}, body=None)

class TraceEventsApiV1TraceEventsGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    pass

class TraceEventsApiV1TraceEventsGetSuccess(RootModel[ResponseEnvelopeListDictStrObject]):
    pass

TraceEventsApiV1TraceEventsGetError = SafeTransportError

TRACEEVENTSAPIV1TRACEEVENTSGET_SECURITY = SecurityMetadata(
    identity='public:trace_events_api_v1_trace_events_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='trace_events_api_v1_trace_events_get', review_owner='Stage 1B0-R7',
)
TRACEEVENTSAPIV1TRACEEVENTSGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0276', operation_id='trace_events_api_v1_trace_events_get',
    method='GET', path='/api/v1/trace/events', backend_tag='trace',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=TraceEventsApiV1TraceEventsGetSuccess, security=TRACEEVENTSAPIV1TRACEEVENTSGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:trace_events_api_v1_trace_events_get',
    response_media_type='application/json',
)
async def trace_events_api_v1_trace_events_get(transport: HttpTransport, request: TraceEventsApiV1TraceEventsGetRequest) -> TraceEventsApiV1TraceEventsGetSuccess:
    return await transport.invoke(TRACEEVENTSAPIV1TRACEEVENTSGET_OPERATION, path_parameters={}, query_parameters={}, body=None)

class TraceEventApiV1TraceEventsEventIdGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    event_id: int

class TraceEventApiV1TraceEventsEventIdGetSuccess(RootModel[ResponseEnvelopeDictStrObject]):
    pass

TraceEventApiV1TraceEventsEventIdGetError = SafeTransportError

TRACEEVENTAPIV1TRACEEVENTSEVENTIDGET_SECURITY = SecurityMetadata(
    identity='public:trace_event_api_v1_trace_events__event_id__get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='trace_event_api_v1_trace_events__event_id__get', review_owner='Stage 1B0-R7',
)
TRACEEVENTAPIV1TRACEEVENTSEVENTIDGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0277', operation_id='trace_event_api_v1_trace_events__event_id__get',
    method='GET', path='/api/v1/trace/events/{event_id}', backend_tag='trace',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=TraceEventApiV1TraceEventsEventIdGetSuccess, security=TRACEEVENTAPIV1TRACEEVENTSEVENTIDGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:trace_event_api_v1_trace_events__event_id__get',
    response_media_type='application/json',
)
async def trace_event_api_v1_trace_events__event_id__get(transport: HttpTransport, request: TraceEventApiV1TraceEventsEventIdGetRequest) -> TraceEventApiV1TraceEventsEventIdGetSuccess:
    return await transport.invoke(TRACEEVENTAPIV1TRACEEVENTSEVENTIDGET_OPERATION, path_parameters={'event_id': str(request.event_id)}, query_parameters={}, body=None)

class LiteAddressCheckApiV1TraceLiteAddressGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    address: str

class LiteAddressCheckApiV1TraceLiteAddressGetSuccess(RootModel[ResponseEnvelopeDictStrObject]):
    pass

LiteAddressCheckApiV1TraceLiteAddressGetError = SafeTransportError

LITEADDRESSCHECKAPIV1TRACELITEADDRESSGET_SECURITY = SecurityMetadata(
    identity='public:lite_address_check_api_v1_trace_lite__address__get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='lite_address_check_api_v1_trace_lite__address__get', review_owner='Stage 1B0-R7',
)
LITEADDRESSCHECKAPIV1TRACELITEADDRESSGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0278', operation_id='lite_address_check_api_v1_trace_lite__address__get',
    method='GET', path='/api/v1/trace/lite/{address}', backend_tag='trace',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=LiteAddressCheckApiV1TraceLiteAddressGetSuccess, security=LITEADDRESSCHECKAPIV1TRACELITEADDRESSGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:lite_address_check_api_v1_trace_lite__address__get',
    response_media_type='application/json',
)
async def lite_address_check_api_v1_trace_lite__address__get(transport: HttpTransport, request: LiteAddressCheckApiV1TraceLiteAddressGetRequest) -> LiteAddressCheckApiV1TraceLiteAddressGetSuccess:
    return await transport.invoke(LITEADDRESSCHECKAPIV1TRACELITEADDRESSGET_OPERATION, path_parameters={'address': str(request.address)}, query_parameters={}, body=None)

class GetReportApiV1TraceReportReportIdGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    report_id: int

class GetReportApiV1TraceReportReportIdGetSuccess(RootModel[ResponseEnvelopeTraceReport]):
    pass

GetReportApiV1TraceReportReportIdGetError = SafeTransportError

GETREPORTAPIV1TRACEREPORTREPORTIDGET_SECURITY = SecurityMetadata(
    identity='public:get_report_api_v1_trace_report__report_id__get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_report_api_v1_trace_report__report_id__get', review_owner='Stage 1B0-R7',
)
GETREPORTAPIV1TRACEREPORTREPORTIDGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0282', operation_id='get_report_api_v1_trace_report__report_id__get',
    method='GET', path='/api/v1/trace/report/{report_id}', backend_tag='trace',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetReportApiV1TraceReportReportIdGetSuccess, security=GETREPORTAPIV1TRACEREPORTREPORTIDGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_report_api_v1_trace_report__report_id__get',
    response_media_type='application/json',
)
async def get_report_api_v1_trace_report__report_id__get(transport: HttpTransport, request: GetReportApiV1TraceReportReportIdGetRequest) -> GetReportApiV1TraceReportReportIdGetSuccess:
    return await transport.invoke(GETREPORTAPIV1TRACEREPORTREPORTIDGET_OPERATION, path_parameters={'report_id': str(request.report_id)}, query_parameters={}, body=None)

class TraceCitadelContributionApiV1TraceReportReportIdCitadelContributionGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    report_id: int

class TraceCitadelContributionApiV1TraceReportReportIdCitadelContributionGetSuccess(RootModel[ResponseEnvelopeDictStrObject]):
    pass

TraceCitadelContributionApiV1TraceReportReportIdCitadelContributionGetError = SafeTransportError

TRACECITADELCONTRIBUTIONAPIV1TRACEREPORTREPORTIDCITADELCONTRIBUTIONGET_SECURITY = SecurityMetadata(
    identity='public:trace_citadel_contribution_api_v1_trace_report__report_id__citadel_contribution_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='trace_citadel_contribution_api_v1_trace_report__report_id__citadel_contribution_get', review_owner='Stage 1B0-R7',
)
TRACECITADELCONTRIBUTIONAPIV1TRACEREPORTREPORTIDCITADELCONTRIBUTIONGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0283', operation_id='trace_citadel_contribution_api_v1_trace_report__report_id__citadel_contribution_get',
    method='GET', path='/api/v1/trace/report/{report_id}/citadel-contribution', backend_tag='trace',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=TraceCitadelContributionApiV1TraceReportReportIdCitadelContributionGetSuccess, security=TRACECITADELCONTRIBUTIONAPIV1TRACEREPORTREPORTIDCITADELCONTRIBUTIONGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:trace_citadel_contribution_api_v1_trace_report__report_id__citadel_contribution_get',
    response_media_type='application/json',
)
async def trace_citadel_contribution_api_v1_trace_report__report_id__citadel_contribution_get(transport: HttpTransport, request: TraceCitadelContributionApiV1TraceReportReportIdCitadelContributionGetRequest) -> TraceCitadelContributionApiV1TraceReportReportIdCitadelContributionGetSuccess:
    return await transport.invoke(TRACECITADELCONTRIBUTIONAPIV1TRACEREPORTREPORTIDCITADELCONTRIBUTIONGET_OPERATION, path_parameters={'report_id': str(request.report_id)}, query_parameters={}, body=None)

class GetCounterpartyLensApiV1TraceReportReportIdCounterpartyLensGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    report_id: int

class GetCounterpartyLensApiV1TraceReportReportIdCounterpartyLensGetSuccess(RootModel[ResponseEnvelopeDictStrObject]):
    pass

GetCounterpartyLensApiV1TraceReportReportIdCounterpartyLensGetError = SafeTransportError

GETCOUNTERPARTYLENSAPIV1TRACEREPORTREPORTIDCOUNTERPARTYLENSGET_SECURITY = SecurityMetadata(
    identity='public:get_counterparty_lens_api_v1_trace_report__report_id__counterparty_lens_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_counterparty_lens_api_v1_trace_report__report_id__counterparty_lens_get', review_owner='Stage 1B0-R7',
)
GETCOUNTERPARTYLENSAPIV1TRACEREPORTREPORTIDCOUNTERPARTYLENSGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0284', operation_id='get_counterparty_lens_api_v1_trace_report__report_id__counterparty_lens_get',
    method='GET', path='/api/v1/trace/report/{report_id}/counterparty-lens', backend_tag='trace',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetCounterpartyLensApiV1TraceReportReportIdCounterpartyLensGetSuccess, security=GETCOUNTERPARTYLENSAPIV1TRACEREPORTREPORTIDCOUNTERPARTYLENSGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_counterparty_lens_api_v1_trace_report__report_id__counterparty_lens_get',
    response_media_type='application/json',
)
async def get_counterparty_lens_api_v1_trace_report__report_id__counterparty_lens_get(transport: HttpTransport, request: GetCounterpartyLensApiV1TraceReportReportIdCounterpartyLensGetRequest) -> GetCounterpartyLensApiV1TraceReportReportIdCounterpartyLensGetSuccess:
    return await transport.invoke(GETCOUNTERPARTYLENSAPIV1TRACEREPORTREPORTIDCOUNTERPARTYLENSGET_OPERATION, path_parameters={'report_id': str(request.report_id)}, query_parameters={}, body=None)

class GetDustRadarApiV1TraceReportReportIdDustRadarGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    report_id: int

class GetDustRadarApiV1TraceReportReportIdDustRadarGetSuccess(RootModel[ResponseEnvelopeDictStrObject]):
    pass

GetDustRadarApiV1TraceReportReportIdDustRadarGetError = SafeTransportError

GETDUSTRADARAPIV1TRACEREPORTREPORTIDDUSTRADARGET_SECURITY = SecurityMetadata(
    identity='public:get_dust_radar_api_v1_trace_report__report_id__dust_radar_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_dust_radar_api_v1_trace_report__report_id__dust_radar_get', review_owner='Stage 1B0-R7',
)
GETDUSTRADARAPIV1TRACEREPORTREPORTIDDUSTRADARGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0285', operation_id='get_dust_radar_api_v1_trace_report__report_id__dust_radar_get',
    method='GET', path='/api/v1/trace/report/{report_id}/dust-radar', backend_tag='trace',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetDustRadarApiV1TraceReportReportIdDustRadarGetSuccess, security=GETDUSTRADARAPIV1TRACEREPORTREPORTIDDUSTRADARGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_dust_radar_api_v1_trace_report__report_id__dust_radar_get',
    response_media_type='application/json',
)
async def get_dust_radar_api_v1_trace_report__report_id__dust_radar_get(transport: HttpTransport, request: GetDustRadarApiV1TraceReportReportIdDustRadarGetRequest) -> GetDustRadarApiV1TraceReportReportIdDustRadarGetSuccess:
    return await transport.invoke(GETDUSTRADARAPIV1TRACEREPORTREPORTIDDUSTRADARGET_OPERATION, path_parameters={'report_id': str(request.report_id)}, query_parameters={}, body=None)

class ListEvidenceApiV1TraceReportReportIdEvidenceGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    report_id: int

class ListEvidenceApiV1TraceReportReportIdEvidenceGetSuccess(RootModel[ResponseEnvelopeListTraceEvidence]):
    pass

ListEvidenceApiV1TraceReportReportIdEvidenceGetError = SafeTransportError

LISTEVIDENCEAPIV1TRACEREPORTREPORTIDEVIDENCEGET_SECURITY = SecurityMetadata(
    identity='public:list_evidence_api_v1_trace_report__report_id__evidence_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='list_evidence_api_v1_trace_report__report_id__evidence_get', review_owner='Stage 1B0-R7',
)
LISTEVIDENCEAPIV1TRACEREPORTREPORTIDEVIDENCEGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0286', operation_id='list_evidence_api_v1_trace_report__report_id__evidence_get',
    method='GET', path='/api/v1/trace/report/{report_id}/evidence', backend_tag='trace',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=ListEvidenceApiV1TraceReportReportIdEvidenceGetSuccess, security=LISTEVIDENCEAPIV1TRACEREPORTREPORTIDEVIDENCEGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:list_evidence_api_v1_trace_report__report_id__evidence_get',
    response_media_type='application/json',
)
async def list_evidence_api_v1_trace_report__report_id__evidence_get(transport: HttpTransport, request: ListEvidenceApiV1TraceReportReportIdEvidenceGetRequest) -> ListEvidenceApiV1TraceReportReportIdEvidenceGetSuccess:
    return await transport.invoke(LISTEVIDENCEAPIV1TRACEREPORTREPORTIDEVIDENCEGET_OPERATION, path_parameters={'report_id': str(request.report_id)}, query_parameters={}, body=None)

class TraceEvidenceRefsApiV1TraceReportReportIdEvidenceRefsGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    report_id: int

class TraceEvidenceRefsApiV1TraceReportReportIdEvidenceRefsGetSuccess(RootModel[ResponseEnvelopeListDictStrObject]):
    pass

TraceEvidenceRefsApiV1TraceReportReportIdEvidenceRefsGetError = SafeTransportError

TRACEEVIDENCEREFSAPIV1TRACEREPORTREPORTIDEVIDENCEREFSGET_SECURITY = SecurityMetadata(
    identity='public:trace_evidence_refs_api_v1_trace_report__report_id__evidence_refs_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='trace_evidence_refs_api_v1_trace_report__report_id__evidence_refs_get', review_owner='Stage 1B0-R7',
)
TRACEEVIDENCEREFSAPIV1TRACEREPORTREPORTIDEVIDENCEREFSGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0287', operation_id='trace_evidence_refs_api_v1_trace_report__report_id__evidence_refs_get',
    method='GET', path='/api/v1/trace/report/{report_id}/evidence-refs', backend_tag='trace',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=TraceEvidenceRefsApiV1TraceReportReportIdEvidenceRefsGetSuccess, security=TRACEEVIDENCEREFSAPIV1TRACEREPORTREPORTIDEVIDENCEREFSGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:trace_evidence_refs_api_v1_trace_report__report_id__evidence_refs_get',
    response_media_type='application/json',
)
async def trace_evidence_refs_api_v1_trace_report__report_id__evidence_refs_get(transport: HttpTransport, request: TraceEvidenceRefsApiV1TraceReportReportIdEvidenceRefsGetRequest) -> TraceEvidenceRefsApiV1TraceReportReportIdEvidenceRefsGetSuccess:
    return await transport.invoke(TRACEEVIDENCEREFSAPIV1TRACEREPORTREPORTIDEVIDENCEREFSGET_OPERATION, path_parameters={'report_id': str(request.report_id)}, query_parameters={}, body=None)

class GetOriginPassportApiV1TraceReportReportIdOriginPassportGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    report_id: int

class GetOriginPassportApiV1TraceReportReportIdOriginPassportGetSuccess(RootModel[ResponseEnvelopeDictStrObject]):
    pass

GetOriginPassportApiV1TraceReportReportIdOriginPassportGetError = SafeTransportError

GETORIGINPASSPORTAPIV1TRACEREPORTREPORTIDORIGINPASSPORTGET_SECURITY = SecurityMetadata(
    identity='public:get_origin_passport_api_v1_trace_report__report_id__origin_passport_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_origin_passport_api_v1_trace_report__report_id__origin_passport_get', review_owner='Stage 1B0-R7',
)
GETORIGINPASSPORTAPIV1TRACEREPORTREPORTIDORIGINPASSPORTGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0288', operation_id='get_origin_passport_api_v1_trace_report__report_id__origin_passport_get',
    method='GET', path='/api/v1/trace/report/{report_id}/origin-passport', backend_tag='trace',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetOriginPassportApiV1TraceReportReportIdOriginPassportGetSuccess, security=GETORIGINPASSPORTAPIV1TRACEREPORTREPORTIDORIGINPASSPORTGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_origin_passport_api_v1_trace_report__report_id__origin_passport_get',
    response_media_type='application/json',
)
async def get_origin_passport_api_v1_trace_report__report_id__origin_passport_get(transport: HttpTransport, request: GetOriginPassportApiV1TraceReportReportIdOriginPassportGetRequest) -> GetOriginPassportApiV1TraceReportReportIdOriginPassportGetSuccess:
    return await transport.invoke(GETORIGINPASSPORTAPIV1TRACEREPORTREPORTIDORIGINPASSPORTGET_OPERATION, path_parameters={'report_id': str(request.report_id)}, query_parameters={}, body=None)

class TracePolicyFactsApiV1TraceReportReportIdPolicyFactsGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    report_id: int

class TracePolicyFactsApiV1TraceReportReportIdPolicyFactsGetSuccess(RootModel[ResponseEnvelopeDictStrObject]):
    pass

TracePolicyFactsApiV1TraceReportReportIdPolicyFactsGetError = SafeTransportError

TRACEPOLICYFACTSAPIV1TRACEREPORTREPORTIDPOLICYFACTSGET_SECURITY = SecurityMetadata(
    identity='public:trace_policy_facts_api_v1_trace_report__report_id__policy_facts_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='trace_policy_facts_api_v1_trace_report__report_id__policy_facts_get', review_owner='Stage 1B0-R7',
)
TRACEPOLICYFACTSAPIV1TRACEREPORTREPORTIDPOLICYFACTSGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0289', operation_id='trace_policy_facts_api_v1_trace_report__report_id__policy_facts_get',
    method='GET', path='/api/v1/trace/report/{report_id}/policy-facts', backend_tag='trace',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=TracePolicyFactsApiV1TraceReportReportIdPolicyFactsGetSuccess, security=TRACEPOLICYFACTSAPIV1TRACEREPORTREPORTIDPOLICYFACTSGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:trace_policy_facts_api_v1_trace_report__report_id__policy_facts_get',
    response_media_type='application/json',
)
async def trace_policy_facts_api_v1_trace_report__report_id__policy_facts_get(transport: HttpTransport, request: TracePolicyFactsApiV1TraceReportReportIdPolicyFactsGetRequest) -> TracePolicyFactsApiV1TraceReportReportIdPolicyFactsGetSuccess:
    return await transport.invoke(TRACEPOLICYFACTSAPIV1TRACEREPORTREPORTIDPOLICYFACTSGET_OPERATION, path_parameters={'report_id': str(request.report_id)}, query_parameters={}, body=None)

class GetPrivacyShieldApiV1TraceReportReportIdPrivacyShieldGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    report_id: int

class GetPrivacyShieldApiV1TraceReportReportIdPrivacyShieldGetSuccess(RootModel[ResponseEnvelopeDictStrObject]):
    pass

GetPrivacyShieldApiV1TraceReportReportIdPrivacyShieldGetError = SafeTransportError

GETPRIVACYSHIELDAPIV1TRACEREPORTREPORTIDPRIVACYSHIELDGET_SECURITY = SecurityMetadata(
    identity='public:get_privacy_shield_api_v1_trace_report__report_id__privacy_shield_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_privacy_shield_api_v1_trace_report__report_id__privacy_shield_get', review_owner='Stage 1B0-R7',
)
GETPRIVACYSHIELDAPIV1TRACEREPORTREPORTIDPRIVACYSHIELDGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0290', operation_id='get_privacy_shield_api_v1_trace_report__report_id__privacy_shield_get',
    method='GET', path='/api/v1/trace/report/{report_id}/privacy-shield', backend_tag='trace',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetPrivacyShieldApiV1TraceReportReportIdPrivacyShieldGetSuccess, security=GETPRIVACYSHIELDAPIV1TRACEREPORTREPORTIDPRIVACYSHIELDGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_privacy_shield_api_v1_trace_report__report_id__privacy_shield_get',
    response_media_type='application/json',
)
async def get_privacy_shield_api_v1_trace_report__report_id__privacy_shield_get(transport: HttpTransport, request: GetPrivacyShieldApiV1TraceReportReportIdPrivacyShieldGetRequest) -> GetPrivacyShieldApiV1TraceReportReportIdPrivacyShieldGetSuccess:
    return await transport.invoke(GETPRIVACYSHIELDAPIV1TRACEREPORTREPORTIDPRIVACYSHIELDGET_OPERATION, path_parameters={'report_id': str(request.report_id)}, query_parameters={}, body=None)

class GetProofPacketApiV1TraceReportReportIdProofPacketGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    report_id: int

class GetProofPacketApiV1TraceReportReportIdProofPacketGetSuccess(RootModel[ResponseEnvelopeDictStrObject]):
    pass

GetProofPacketApiV1TraceReportReportIdProofPacketGetError = SafeTransportError

GETPROOFPACKETAPIV1TRACEREPORTREPORTIDPROOFPACKETGET_SECURITY = SecurityMetadata(
    identity='public:get_proof_packet_api_v1_trace_report__report_id__proof_packet_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_proof_packet_api_v1_trace_report__report_id__proof_packet_get', review_owner='Stage 1B0-R7',
)
GETPROOFPACKETAPIV1TRACEREPORTREPORTIDPROOFPACKETGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0291', operation_id='get_proof_packet_api_v1_trace_report__report_id__proof_packet_get',
    method='GET', path='/api/v1/trace/report/{report_id}/proof-packet', backend_tag='trace',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetProofPacketApiV1TraceReportReportIdProofPacketGetSuccess, security=GETPROOFPACKETAPIV1TRACEREPORTREPORTIDPROOFPACKETGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_proof_packet_api_v1_trace_report__report_id__proof_packet_get',
    response_media_type='application/json',
)
async def get_proof_packet_api_v1_trace_report__report_id__proof_packet_get(transport: HttpTransport, request: GetProofPacketApiV1TraceReportReportIdProofPacketGetRequest) -> GetProofPacketApiV1TraceReportReportIdProofPacketGetSuccess:
    return await transport.invoke(GETPROOFPACKETAPIV1TRACEREPORTREPORTIDPROOFPACKETGET_OPERATION, path_parameters={'report_id': str(request.report_id)}, query_parameters={}, body=None)

class GetProviderDisagreementApiV1TraceReportReportIdProviderDisagreementGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    report_id: int

class GetProviderDisagreementApiV1TraceReportReportIdProviderDisagreementGetSuccess(RootModel[ResponseEnvelopeDictStrObject]):
    pass

GetProviderDisagreementApiV1TraceReportReportIdProviderDisagreementGetError = SafeTransportError

GETPROVIDERDISAGREEMENTAPIV1TRACEREPORTREPORTIDPROVIDERDISAGREEMENTGET_SECURITY = SecurityMetadata(
    identity='public:get_provider_disagreement_api_v1_trace_report__report_id__provider_disagreement_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_provider_disagreement_api_v1_trace_report__report_id__provider_disagreement_get', review_owner='Stage 1B0-R7',
)
GETPROVIDERDISAGREEMENTAPIV1TRACEREPORTREPORTIDPROVIDERDISAGREEMENTGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0292', operation_id='get_provider_disagreement_api_v1_trace_report__report_id__provider_disagreement_get',
    method='GET', path='/api/v1/trace/report/{report_id}/provider-disagreement', backend_tag='trace',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetProviderDisagreementApiV1TraceReportReportIdProviderDisagreementGetSuccess, security=GETPROVIDERDISAGREEMENTAPIV1TRACEREPORTREPORTIDPROVIDERDISAGREEMENTGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_provider_disagreement_api_v1_trace_report__report_id__provider_disagreement_get',
    response_media_type='application/json',
)
async def get_provider_disagreement_api_v1_trace_report__report_id__provider_disagreement_get(transport: HttpTransport, request: GetProviderDisagreementApiV1TraceReportReportIdProviderDisagreementGetRequest) -> GetProviderDisagreementApiV1TraceReportReportIdProviderDisagreementGetSuccess:
    return await transport.invoke(GETPROVIDERDISAGREEMENTAPIV1TRACEREPORTREPORTIDPROVIDERDISAGREEMENTGET_OPERATION, path_parameters={'report_id': str(request.report_id)}, query_parameters={}, body=None)

class GetSourceSummaryApiV1TraceReportReportIdSourceSummaryGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    report_id: int

class GetSourceSummaryApiV1TraceReportReportIdSourceSummaryGetSuccess(RootModel[ResponseEnvelopeListDictStrObject]):
    pass

GetSourceSummaryApiV1TraceReportReportIdSourceSummaryGetError = SafeTransportError

GETSOURCESUMMARYAPIV1TRACEREPORTREPORTIDSOURCESUMMARYGET_SECURITY = SecurityMetadata(
    identity='public:get_source_summary_api_v1_trace_report__report_id__source_summary_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_source_summary_api_v1_trace_report__report_id__source_summary_get', review_owner='Stage 1B0-R7',
)
GETSOURCESUMMARYAPIV1TRACEREPORTREPORTIDSOURCESUMMARYGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0293', operation_id='get_source_summary_api_v1_trace_report__report_id__source_summary_get',
    method='GET', path='/api/v1/trace/report/{report_id}/source-summary', backend_tag='trace',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetSourceSummaryApiV1TraceReportReportIdSourceSummaryGetSuccess, security=GETSOURCESUMMARYAPIV1TRACEREPORTREPORTIDSOURCESUMMARYGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_source_summary_api_v1_trace_report__report_id__source_summary_get',
    response_media_type='application/json',
)
async def get_source_summary_api_v1_trace_report__report_id__source_summary_get(transport: HttpTransport, request: GetSourceSummaryApiV1TraceReportReportIdSourceSummaryGetRequest) -> GetSourceSummaryApiV1TraceReportReportIdSourceSummaryGetSuccess:
    return await transport.invoke(GETSOURCESUMMARYAPIV1TRACEREPORTREPORTIDSOURCESUMMARYGET_OPERATION, path_parameters={'report_id': str(request.report_id)}, query_parameters={}, body=None)

class GetUtxoHygieneApiV1TraceReportReportIdUtxoHygieneGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    report_id: int

class GetUtxoHygieneApiV1TraceReportReportIdUtxoHygieneGetSuccess(RootModel[ResponseEnvelopeDictStrObject]):
    pass

GetUtxoHygieneApiV1TraceReportReportIdUtxoHygieneGetError = SafeTransportError

GETUTXOHYGIENEAPIV1TRACEREPORTREPORTIDUTXOHYGIENEGET_SECURITY = SecurityMetadata(
    identity='public:get_utxo_hygiene_api_v1_trace_report__report_id__utxo_hygiene_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_utxo_hygiene_api_v1_trace_report__report_id__utxo_hygiene_get', review_owner='Stage 1B0-R7',
)
GETUTXOHYGIENEAPIV1TRACEREPORTREPORTIDUTXOHYGIENEGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0294', operation_id='get_utxo_hygiene_api_v1_trace_report__report_id__utxo_hygiene_get',
    method='GET', path='/api/v1/trace/report/{report_id}/utxo-hygiene', backend_tag='trace',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetUtxoHygieneApiV1TraceReportReportIdUtxoHygieneGetSuccess, security=GETUTXOHYGIENEAPIV1TRACEREPORTREPORTIDUTXOHYGIENEGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_utxo_hygiene_api_v1_trace_report__report_id__utxo_hygiene_get',
    response_media_type='application/json',
)
async def get_utxo_hygiene_api_v1_trace_report__report_id__utxo_hygiene_get(transport: HttpTransport, request: GetUtxoHygieneApiV1TraceReportReportIdUtxoHygieneGetRequest) -> GetUtxoHygieneApiV1TraceReportReportIdUtxoHygieneGetSuccess:
    return await transport.invoke(GETUTXOHYGIENEAPIV1TRACEREPORTREPORTIDUTXOHYGIENEGET_OPERATION, path_parameters={'report_id': str(request.report_id)}, query_parameters={}, body=None)

class ListSourcesApiV1TraceSourcesGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    pass

class ListSourcesApiV1TraceSourcesGetSuccess(RootModel[ResponseEnvelopeListTraceSourceStatus]):
    pass

ListSourcesApiV1TraceSourcesGetError = SafeTransportError

LISTSOURCESAPIV1TRACESOURCESGET_SECURITY = SecurityMetadata(
    identity='public:list_sources_api_v1_trace_sources_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='list_sources_api_v1_trace_sources_get', review_owner='Stage 1B0-R7',
)
LISTSOURCESAPIV1TRACESOURCESGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0295', operation_id='list_sources_api_v1_trace_sources_get',
    method='GET', path='/api/v1/trace/sources', backend_tag='trace',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=ListSourcesApiV1TraceSourcesGetSuccess, security=LISTSOURCESAPIV1TRACESOURCESGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:list_sources_api_v1_trace_sources_get',
    response_media_type='application/json',
)
async def list_sources_api_v1_trace_sources_get(transport: HttpTransport, request: ListSourcesApiV1TraceSourcesGetRequest) -> ListSourcesApiV1TraceSourcesGetSuccess:
    return await transport.invoke(LISTSOURCESAPIV1TRACESOURCESGET_OPERATION, path_parameters={}, query_parameters={}, body=None)

class GetSourceApiV1TraceSourcesSourceNameGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    source_name: str

class GetSourceApiV1TraceSourcesSourceNameGetSuccess(RootModel[ResponseEnvelopeTraceSourceStatus]):
    pass

GetSourceApiV1TraceSourcesSourceNameGetError = SafeTransportError

GETSOURCEAPIV1TRACESOURCESSOURCENAMEGET_SECURITY = SecurityMetadata(
    identity='public:get_source_api_v1_trace_sources__source_name__get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='get_source_api_v1_trace_sources__source_name__get', review_owner='Stage 1B0-R7',
)
GETSOURCEAPIV1TRACESOURCESSOURCENAMEGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0296', operation_id='get_source_api_v1_trace_sources__source_name__get',
    method='GET', path='/api/v1/trace/sources/{source_name}', backend_tag='trace',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=GetSourceApiV1TraceSourcesSourceNameGetSuccess, security=GETSOURCEAPIV1TRACESOURCESSOURCENAMEGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:get_source_api_v1_trace_sources__source_name__get',
    response_media_type='application/json',
)
async def get_source_api_v1_trace_sources__source_name__get(transport: HttpTransport, request: GetSourceApiV1TraceSourcesSourceNameGetRequest) -> GetSourceApiV1TraceSourcesSourceNameGetSuccess:
    return await transport.invoke(GETSOURCEAPIV1TRACESOURCESSOURCENAMEGET_OPERATION, path_parameters={'source_name': str(request.source_name)}, query_parameters={}, body=None)

class TraceStatusApiV1TraceStatusGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    pass

class TraceStatusApiV1TraceStatusGetSuccess(RootModel[ResponseEnvelopeDictStrObject]):
    pass

TraceStatusApiV1TraceStatusGetError = SafeTransportError

TRACESTATUSAPIV1TRACESTATUSGET_SECURITY = SecurityMetadata(
    identity='public:trace_status_api_v1_trace_status_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='trace_status_api_v1_trace_status_get', review_owner='Stage 1B0-R7',
)
TRACESTATUSAPIV1TRACESTATUSGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0297', operation_id='trace_status_api_v1_trace_status_get',
    method='GET', path='/api/v1/trace/status', backend_tag='trace',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=TraceStatusApiV1TraceStatusGetSuccess, security=TRACESTATUSAPIV1TRACESTATUSGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:trace_status_api_v1_trace_status_get',
    response_media_type='application/json',
)
async def trace_status_api_v1_trace_status_get(transport: HttpTransport, request: TraceStatusApiV1TraceStatusGetRequest) -> TraceStatusApiV1TraceStatusGetSuccess:
    return await transport.invoke(TRACESTATUSAPIV1TRACESTATUSGET_OPERATION, path_parameters={}, query_parameters={}, body=None)

class ListWatchlistApiV1TraceWatchlistGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    pass

class ListWatchlistApiV1TraceWatchlistGetSuccess(RootModel[ResponseEnvelopeListTraceWatchlistEntry]):
    pass

ListWatchlistApiV1TraceWatchlistGetError = SafeTransportError

LISTWATCHLISTAPIV1TRACEWATCHLISTGET_SECURITY = SecurityMetadata(
    identity='public:list_watchlist_api_v1_trace_watchlist_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='list_watchlist_api_v1_trace_watchlist_get', review_owner='Stage 1B0-R7',
)
LISTWATCHLISTAPIV1TRACEWATCHLISTGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0299', operation_id='list_watchlist_api_v1_trace_watchlist_get',
    method='GET', path='/api/v1/trace/watchlist', backend_tag='trace',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=ListWatchlistApiV1TraceWatchlistGetSuccess, security=LISTWATCHLISTAPIV1TRACEWATCHLISTGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:list_watchlist_api_v1_trace_watchlist_get',
    response_media_type='application/json',
)
async def list_watchlist_api_v1_trace_watchlist_get(transport: HttpTransport, request: ListWatchlistApiV1TraceWatchlistGetRequest) -> ListWatchlistApiV1TraceWatchlistGetSuccess:
    return await transport.invoke(LISTWATCHLISTAPIV1TRACEWATCHLISTGET_OPERATION, path_parameters={}, query_parameters={}, body=None)

class DependenciesHealthDependenciesGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    pass

class DependenciesHealthDependenciesGetSuccess(RootModel[list[DependencyHealthOut]]):
    pass

DependenciesHealthDependenciesGetError = SafeTransportError

DEPENDENCIESHEALTHDEPENDENCIESGET_SECURITY = SecurityMetadata(
    identity='public:dependencies_health_dependencies_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='dependencies_health_dependencies_get', review_owner='Stage 1B0-R7',
)
DEPENDENCIESHEALTHDEPENDENCIESGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0341', operation_id='dependencies_health_dependencies_get',
    method='GET', path='/health/dependencies', backend_tag='root-health',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=DependenciesHealthDependenciesGetSuccess, security=DEPENDENCIESHEALTHDEPENDENCIESGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:dependencies_health_dependencies_get',
    response_media_type='application/json',
)
async def dependencies_health_dependencies_get(transport: HttpTransport, request: DependenciesHealthDependenciesGetRequest) -> DependenciesHealthDependenciesGetSuccess:
    return await transport.invoke(DEPENDENCIESHEALTHDEPENDENCIESGET_OPERATION, path_parameters={}, query_parameters={}, body=None)

class IntelligenceHealthIntelligenceGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    pass

class IntelligenceHealthIntelligenceGetSuccess(RootModel[IntelligenceHealthOut]):
    pass

IntelligenceHealthIntelligenceGetError = SafeTransportError

INTELLIGENCEHEALTHINTELLIGENCEGET_SECURITY = SecurityMetadata(
    identity='public:intelligence_health_intelligence_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='intelligence_health_intelligence_get', review_owner='Stage 1B0-R7',
)
INTELLIGENCEHEALTHINTELLIGENCEGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0342', operation_id='intelligence_health_intelligence_get',
    method='GET', path='/health/intelligence', backend_tag='root-health',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=IntelligenceHealthIntelligenceGetSuccess, security=INTELLIGENCEHEALTHINTELLIGENCEGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:intelligence_health_intelligence_get',
    response_media_type='application/json',
)
async def intelligence_health_intelligence_get(transport: HttpTransport, request: IntelligenceHealthIntelligenceGetRequest) -> IntelligenceHealthIntelligenceGetSuccess:
    return await transport.invoke(INTELLIGENCEHEALTHINTELLIGENCEGET_OPERATION, path_parameters={}, query_parameters={}, body=None)

class LiveHealthLiveGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    pass

class LiveHealthLiveGetSuccess(RootModel[HealthOut]):
    pass

LiveHealthLiveGetError = SafeTransportError

LIVEHEALTHLIVEGET_SECURITY = SecurityMetadata(
    identity='public:live_health_live_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='live_health_live_get', review_owner='Stage 1B0-R7',
)
LIVEHEALTHLIVEGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0343', operation_id='live_health_live_get',
    method='GET', path='/health/live', backend_tag='root-health',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=LiveHealthLiveGetSuccess, security=LIVEHEALTHLIVEGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:live_health_live_get',
    response_media_type='application/json',
)
async def live_health_live_get(transport: HttpTransport, request: LiveHealthLiveGetRequest) -> LiveHealthLiveGetSuccess:
    return await transport.invoke(LIVEHEALTHLIVEGET_OPERATION, path_parameters={}, query_parameters={}, body=None)

class OperationsHealthOperationsGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    pass

class OperationsHealthOperationsGetSuccess(RootModel[OperationsHealthOut]):
    pass

OperationsHealthOperationsGetError = SafeTransportError

OPERATIONSHEALTHOPERATIONSGET_SECURITY = SecurityMetadata(
    identity='public:operations_health_operations_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='operations_health_operations_get', review_owner='Stage 1B0-R7',
)
OPERATIONSHEALTHOPERATIONSGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0344', operation_id='operations_health_operations_get',
    method='GET', path='/health/operations', backend_tag='root-health',
    product='Operator Console', disposition='UI_REQUIRED',
    success_status=200, response_type=OperationsHealthOperationsGetSuccess, security=OPERATIONSHEALTHOPERATIONSGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:operations_health_operations_get',
    response_media_type='application/json',
)
async def operations_health_operations_get(transport: HttpTransport, request: OperationsHealthOperationsGetRequest) -> OperationsHealthOperationsGetSuccess:
    return await transport.invoke(OPERATIONSHEALTHOPERATIONSGET_OPERATION, path_parameters={}, query_parameters={}, body=None)

class ProvidersHealthProvidersGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    pass

class ProvidersHealthProvidersGetSuccess(RootModel[list[ProviderHealthSnapshotOut]]):
    pass

ProvidersHealthProvidersGetError = SafeTransportError

PROVIDERSHEALTHPROVIDERSGET_SECURITY = SecurityMetadata(
    identity='public:providers_health_providers_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='providers_health_providers_get', review_owner='Stage 1B0-R7',
)
PROVIDERSHEALTHPROVIDERSGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0345', operation_id='providers_health_providers_get',
    method='GET', path='/health/providers', backend_tag='root-health',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=ProvidersHealthProvidersGetSuccess, security=PROVIDERSHEALTHPROVIDERSGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:providers_health_providers_get',
    response_media_type='application/json',
)
async def providers_health_providers_get(transport: HttpTransport, request: ProvidersHealthProvidersGetRequest) -> ProvidersHealthProvidersGetSuccess:
    return await transport.invoke(PROVIDERSHEALTHPROVIDERSGET_OPERATION, path_parameters={}, query_parameters={}, body=None)

class ReadyHealthReadyGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    pass

class ReadyHealthReadyGetSuccess(RootModel[OperationsHealthOut]):
    pass

ReadyHealthReadyGetError = SafeTransportError

READYHEALTHREADYGET_SECURITY = SecurityMetadata(
    identity='public:ready_health_ready_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='ready_health_ready_get', review_owner='Stage 1B0-R7',
)
READYHEALTHREADYGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0346', operation_id='ready_health_ready_get',
    method='GET', path='/health/ready', backend_tag='root-health',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=ReadyHealthReadyGetSuccess, security=READYHEALTHREADYGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:ready_health_ready_get',
    response_media_type='application/json',
)
async def ready_health_ready_get(transport: HttpTransport, request: ReadyHealthReadyGetRequest) -> ReadyHealthReadyGetSuccess:
    return await transport.invoke(READYHEALTHREADYGET_OPERATION, path_parameters={}, query_parameters={}, body=None)

class StartupHealthStartupGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    pass

class StartupHealthStartupGetSuccess(RootModel[HealthOut]):
    pass

StartupHealthStartupGetError = SafeTransportError

STARTUPHEALTHSTARTUPGET_SECURITY = SecurityMetadata(
    identity='public:startup_health_startup_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='startup_health_startup_get', review_owner='Stage 1B0-R7',
)
STARTUPHEALTHSTARTUPGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0347', operation_id='startup_health_startup_get',
    method='GET', path='/health/startup', backend_tag='root-health',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=StartupHealthStartupGetSuccess, security=STARTUPHEALTHSTARTUPGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:startup_health_startup_get',
    response_media_type='application/json',
)
async def startup_health_startup_get(transport: HttpTransport, request: StartupHealthStartupGetRequest) -> StartupHealthStartupGetSuccess:
    return await transport.invoke(STARTUPHEALTHSTARTUPGET_OPERATION, path_parameters={}, query_parameters={}, body=None)

class WebCandleDtoWebCandleCandleIdGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    candle_id: int

class WebCandleDtoWebCandleCandleIdGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

WebCandleDtoWebCandleCandleIdGetError = SafeTransportError

WEBCANDLEDTOWEBCANDLECANDLEIDGET_SECURITY = SecurityMetadata(
    identity='public:web_candle_dto_web_candle__candle_id__get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='web_candle_dto_web_candle__candle_id__get', review_owner='Stage 1B0-R7',
)
WEBCANDLEDTOWEBCANDLECANDLEIDGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0362', operation_id='web_candle_dto_web_candle__candle_id__get',
    method='GET', path='/web/candle/{candle_id}', backend_tag='market-intelligence-web',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=WebCandleDtoWebCandleCandleIdGetSuccess, security=WEBCANDLEDTOWEBCANDLECANDLEIDGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:web_candle_dto_web_candle__candle_id__get',
    response_media_type='application/json',
)
async def web_candle_dto_web_candle__candle_id__get(transport: HttpTransport, request: WebCandleDtoWebCandleCandleIdGetRequest) -> WebCandleDtoWebCandleCandleIdGetSuccess:
    return await transport.invoke(WEBCANDLEDTOWEBCANDLECANDLEIDGET_OPERATION, path_parameters={'candle_id': str(request.candle_id)}, query_parameters={}, body=None)

class WebEvidenceDtoWebEvidencePacketIdGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    packet_id: int

class WebEvidenceDtoWebEvidencePacketIdGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

WebEvidenceDtoWebEvidencePacketIdGetError = SafeTransportError

WEBEVIDENCEDTOWEBEVIDENCEPACKETIDGET_SECURITY = SecurityMetadata(
    identity='public:web_evidence_dto_web_evidence__packet_id__get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='web_evidence_dto_web_evidence__packet_id__get', review_owner='Stage 1B0-R7',
)
WEBEVIDENCEDTOWEBEVIDENCEPACKETIDGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0363', operation_id='web_evidence_dto_web_evidence__packet_id__get',
    method='GET', path='/web/evidence/{packet_id}', backend_tag='market-intelligence-web',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=WebEvidenceDtoWebEvidencePacketIdGetSuccess, security=WEBEVIDENCEDTOWEBEVIDENCEPACKETIDGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:web_evidence_dto_web_evidence__packet_id__get',
    response_media_type='application/json',
)
async def web_evidence_dto_web_evidence__packet_id__get(transport: HttpTransport, request: WebEvidenceDtoWebEvidencePacketIdGetRequest) -> WebEvidenceDtoWebEvidencePacketIdGetSuccess:
    return await transport.invoke(WEBEVIDENCEDTOWEBEVIDENCEPACKETIDGET_OPERATION, path_parameters={'packet_id': str(request.packet_id)}, query_parameters={}, body=None)

class WebMarketTimeMachineDtoWebMarketTimeMachineGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    timeframe: str | None = None

class WebMarketTimeMachineDtoWebMarketTimeMachineGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

WebMarketTimeMachineDtoWebMarketTimeMachineGetError = SafeTransportError

WEBMARKETTIMEMACHINEDTOWEBMARKETTIMEMACHINEGET_SECURITY = SecurityMetadata(
    identity='public:web_market_time_machine_dto_web_market_time_machine_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='web_market_time_machine_dto_web_market_time_machine_get', review_owner='Stage 1B0-R7',
)
WEBMARKETTIMEMACHINEDTOWEBMARKETTIMEMACHINEGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0364', operation_id='web_market_time_machine_dto_web_market_time_machine_get',
    method='GET', path='/web/market-time-machine', backend_tag='market-intelligence-web',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=WebMarketTimeMachineDtoWebMarketTimeMachineGetSuccess, security=WEBMARKETTIMEMACHINEDTOWEBMARKETTIMEMACHINEGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:web_market_time_machine_dto_web_market_time_machine_get',
    response_media_type='application/json',
)
async def web_market_time_machine_dto_web_market_time_machine_get(transport: HttpTransport, request: WebMarketTimeMachineDtoWebMarketTimeMachineGetRequest) -> WebMarketTimeMachineDtoWebMarketTimeMachineGetSuccess:
    return await transport.invoke(WEBMARKETTIMEMACHINEDTOWEBMARKETTIMEMACHINEGET_OPERATION, path_parameters={}, query_parameters={'timeframe': serialize_query_value(request.timeframe)}, body=None)

class WebTimelineDtoWebTimelineGetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    filter: str | None = None
    page: int | None = None
    page_size: int | None = None
    sort: str | None = None
    window: str | None = None

class WebTimelineDtoWebTimelineGetSuccess(RootModel[dict[str, JsonValue]]):
    pass

WebTimelineDtoWebTimelineGetError = SafeTransportError

WEBTIMELINEDTOWEBTIMELINEGET_SECURITY = SecurityMetadata(
    identity='public:web_timeline_dto_web_timeline_get', public=True, access_required=False,
    signed_request_required=False, human_intent_required=False,
    source_symbol='web_timeline_dto_web_timeline_get', review_owner='Stage 1B0-R7',
)
WEBTIMELINEDTOWEBTIMELINEGET_OPERATION = NormalizedOperation(
    matrix_id='HTTP-0369', operation_id='web_timeline_dto_web_timeline_get',
    method='GET', path='/web/timeline', backend_tag='market-intelligence-web',
    product='Core', disposition='UI_REQUIRED',
    success_status=200, response_type=WebTimelineDtoWebTimelineGetSuccess, security=WEBTIMELINEDTOWEBTIMELINEGET_SECURITY,
    retry_safe=True, owner='bastion_ui.transport.generated_http:web_timeline_dto_web_timeline_get',
    response_media_type='application/json',
)
async def web_timeline_dto_web_timeline_get(transport: HttpTransport, request: WebTimelineDtoWebTimelineGetRequest) -> WebTimelineDtoWebTimelineGetSuccess:
    return await transport.invoke(WEBTIMELINEDTOWEBTIMELINEGET_OPERATION, path_parameters={}, query_parameters={'filter': serialize_query_value(request.filter), 'page': serialize_query_value(request.page), 'page_size': serialize_query_value(request.page_size), 'sort': serialize_query_value(request.sort), 'window': serialize_query_value(request.window)}, body=None)

SOURCE_HEAD = '818acbe761a20b84940ba9493076c09a78bbc22e'

OWNERSHIP = {
    'list_child_api_keys_api_v1_access_api_keys_get': ('HTTP-0002', 'bastion_ui.transport.generated_http', 'list_child_api_keys_api_v1_access_api_keys_get'),
    'get_child_api_key_api_v1_access_api_keys__key_id__get': ('HTTP-0005', 'bastion_ui.transport.generated_http', 'get_child_api_key_api_v1_access_api_keys__key_id__get'),
    'list_delegated_passes_api_v1_access_delegated_passes_get': ('HTTP-0010', 'bastion_ui.transport.generated_http', 'list_delegated_passes_api_v1_access_delegated_passes_get'),
    'get_delegated_pass_api_v1_access_delegated_passes__delegated_pass_id__get': ('HTTP-0013', 'bastion_ui.transport.generated_http', 'get_delegated_pass_api_v1_access_delegated_passes__delegated_pass_id__get'),
    'get_human_intent_api_v1_access_intents__intent_id__get': ('HTTP-0016', 'bastion_ui.transport.generated_http', 'get_human_intent_api_v1_access_intents__intent_id__get'),
    'get_me_api_v1_access_me_get': ('HTTP-0019', 'bastion_ui.transport.generated_http', 'get_me_api_v1_access_me_get'),
    'get_my_entitlements_api_v1_access_me_entitlements_get': ('HTTP-0020', 'bastion_ui.transport.generated_http', 'get_my_entitlements_api_v1_access_me_entitlements_get'),
    'get_my_limits_api_v1_access_me_limits_get': ('HTTP-0021', 'bastion_ui.transport.generated_http', 'get_my_limits_api_v1_access_me_limits_get'),
    'get_payment_intent_status_api_v1_access_payment_intents__payment_intent_id__get': ('HTTP-0023', 'bastion_ui.transport.generated_http', 'get_payment_intent_status_api_v1_access_payment_intents__payment_intent_id__get'),
    'recovery_status_api_v1_access_recovery_status__recovery_attempt_id__get': ('HTTP-0031', 'bastion_ui.transport.generated_http', 'recovery_status_api_v1_access_recovery_status__recovery_attempt_id__get'),
    'list_addresses_api_v1_business_lightning_addresses_get': ('HTTP-0041', 'bastion_ui.transport.generated_http', 'list_addresses_api_v1_business_lightning_addresses_get'),
    'get_address_api_v1_business_lightning_addresses__address_id__get': ('HTTP-0044', 'bastion_ui.transport.generated_http', 'get_address_api_v1_business_lightning_addresses__address_id__get'),
    'list_domains_api_v1_business_lightning_domains_get': ('HTTP-0047', 'bastion_ui.transport.generated_http', 'list_domains_api_v1_business_lightning_domains_get'),
    'get_domain_api_v1_business_lightning_domains__domain_id__get': ('HTTP-0050', 'bastion_ui.transport.generated_http', 'get_domain_api_v1_business_lightning_domains__domain_id__get'),
    'citadel_assessment_api_v1_citadel_assessment_get': ('HTTP-0053', 'bastion_ui.transport.generated_http', 'citadel_assessment_api_v1_citadel_assessment_get'),
    'citadel_dependencies_api_v1_citadel_dependencies_get': ('HTTP-0054', 'bastion_ui.transport.generated_http', 'citadel_dependencies_api_v1_citadel_dependencies_get'),
    'citadel_inheritance_api_v1_citadel_inheritance_get': ('HTTP-0055', 'bastion_ui.transport.generated_http', 'citadel_inheritance_api_v1_citadel_inheritance_get'),
    'citadel_overview_api_v1_citadel_overview_get': ('HTTP-0056', 'bastion_ui.transport.generated_http', 'citadel_overview_api_v1_citadel_overview_get'),
    'citadel_policy_checks_api_v1_citadel_policy_checks_get': ('HTTP-0057', 'bastion_ui.transport.generated_http', 'citadel_policy_checks_api_v1_citadel_policy_checks_get'),
    'citadel_recovery_api_v1_citadel_recovery_get': ('HTTP-0059', 'bastion_ui.transport.generated_http', 'citadel_recovery_api_v1_citadel_recovery_get'),
    'citadel_repair_plan_api_v1_citadel_repair_plan_get': ('HTTP-0060', 'bastion_ui.transport.generated_http', 'citadel_repair_plan_api_v1_citadel_repair_plan_get'),
    'list_simulations_api_v1_citadel_simulations_get': ('HTTP-0061', 'bastion_ui.transport.generated_http', 'list_simulations_api_v1_citadel_simulations_get'),
    'list_snippets_api_v1_education_snippets_get': ('HTTP-0063', 'bastion_ui.transport.generated_http', 'list_snippets_api_v1_education_snippets_get'),
    'list_entities_api_v1_entities_get': ('HTTP-0064', 'bastion_ui.transport.generated_http', 'list_entities_api_v1_entities_get'),
    'get_market_memory_evidence_api_v1_evidence_market_memory__event_id__get': ('HTTP-0067', 'bastion_ui.transport.generated_http', 'get_market_memory_evidence_api_v1_evidence_market_memory__event_id__get'),
    'list_evidence_packets_api_v1_evidence_packets_get': ('HTTP-0068', 'bastion_ui.transport.generated_http', 'list_evidence_packets_api_v1_evidence_packets_get'),
    'get_evidence_packet_api_v1_evidence_packets__packet_id__get': ('HTTP-0069', 'bastion_ui.transport.generated_http', 'get_evidence_packet_api_v1_evidence_packets__packet_id__get'),
    'get_evidence_packet_relationships_api_v1_evidence_packets__packet_id__relationships_get': ('HTTP-0070', 'bastion_ui.transport.generated_http', 'get_evidence_packet_relationships_api_v1_evidence_packets__packet_id__relationships_get'),
    'get_evidence_packet_timeline_api_v1_evidence_packets__packet_id__timeline_get': ('HTTP-0071', 'bastion_ui.transport.generated_http', 'get_evidence_packet_timeline_api_v1_evidence_packets__packet_id__timeline_get'),
    'replay_evidence_api_v1_evidence_replay__entity_type___entity_id__get': ('HTTP-0072', 'bastion_ui.transport.generated_http', 'replay_evidence_api_v1_evidence_replay__entity_type___entity_id__get'),
    'replay_evidence_integrity_api_v1_evidence_replay__entity_type___entity_id__integrity_get': ('HTTP-0073', 'bastion_ui.transport.generated_http', 'replay_evidence_integrity_api_v1_evidence_replay__entity_type___entity_id__integrity_get'),
    'replay_evidence_timeline_api_v1_evidence_replay__entity_type___entity_id__timeline_get': ('HTTP-0074', 'bastion_ui.transport.generated_http', 'replay_evidence_timeline_api_v1_evidence_replay__entity_type___entity_id__timeline_get'),
    'health_api_v1_health_get': ('HTTP-0076', 'bastion_ui.transport.generated_http', 'health_api_v1_health_get'),
    'degraded_api_v1_health_degraded_get': ('HTTP-0077', 'bastion_ui.transport.generated_http', 'degraded_api_v1_health_degraded_get'),
    'jobs_api_v1_health_jobs_get': ('HTTP-0078', 'bastion_ui.transport.generated_http', 'jobs_api_v1_health_jobs_get'),
    'liveness_api_v1_health_live_get': ('HTTP-0079', 'bastion_ui.transport.generated_http', 'liveness_api_v1_health_live_get'),
    'providers_api_v1_health_providers_get': ('HTTP-0080', 'bastion_ui.transport.generated_http', 'providers_api_v1_health_providers_get'),
    'readiness_api_v1_health_ready_get': ('HTTP-0081', 'bastion_ui.transport.generated_http', 'readiness_api_v1_health_ready_get'),
    'runtime_api_v1_health_runtime_get': ('HTTP-0082', 'bastion_ui.transport.generated_http', 'runtime_api_v1_health_runtime_get'),
    'system_health_api_v1_health_system_get': ('HTTP-0083', 'bastion_ui.transport.generated_http', 'system_health_api_v1_health_system_get'),
    'get_candle_dashboard_dto_api_v1_intelligence_candles__candle_id__get': ('HTTP-0085', 'bastion_ui.transport.generated_http', 'get_candle_dashboard_dto_api_v1_intelligence_candles__candle_id__get'),
    'get_candle_attribution_api_v1_intelligence_candles__candle_id__attribution_get': ('HTTP-0086', 'bastion_ui.transport.generated_http', 'get_candle_attribution_api_v1_intelligence_candles__candle_id__attribution_get'),
    'get_candle_candidates_api_v1_intelligence_candles__candle_id__candidates_get': ('HTTP-0087', 'bastion_ui.transport.generated_http', 'get_candle_candidates_api_v1_intelligence_candles__candle_id__candidates_get'),
    'get_candle_context_api_v1_intelligence_candles__candle_id__context_get': ('HTTP-0088', 'bastion_ui.transport.generated_http', 'get_candle_context_api_v1_intelligence_candles__candle_id__context_get'),
    'get_candle_events_dashboard_dto_api_v1_intelligence_candles__candle_id__events_get': ('HTTP-0089', 'bastion_ui.transport.generated_http', 'get_candle_events_dashboard_dto_api_v1_intelligence_candles__candle_id__events_get'),
    'get_candle_evidence_dashboard_dto_api_v1_intelligence_candles__candle_id__evidence_get': ('HTTP-0090', 'bastion_ui.transport.generated_http', 'get_candle_evidence_dashboard_dto_api_v1_intelligence_candles__candle_id__evidence_get'),
    'explain_candle_api_v1_intelligence_candles__candle_id__explain_get': ('HTTP-0091', 'bastion_ui.transport.generated_http', 'explain_candle_api_v1_intelligence_candles__candle_id__explain_get'),
    'get_candle_replay_api_v1_intelligence_candles__candle_id__replay_get': ('HTTP-0092', 'bastion_ui.transport.generated_http', 'get_candle_replay_api_v1_intelligence_candles__candle_id__replay_get'),
    'get_candle_similarity_dashboard_dto_api_v1_intelligence_candles__candle_id__similar_get': ('HTTP-0093', 'bastion_ui.transport.generated_http', 'get_candle_similarity_dashboard_dto_api_v1_intelligence_candles__candle_id__similar_get'),
    'get_candle_top_events_api_v1_intelligence_candles__candle_id__top_events_get': ('HTTP-0094', 'bastion_ui.transport.generated_http', 'get_candle_top_events_api_v1_intelligence_candles__candle_id__top_events_get'),
    'get_event_market_memory_api_v1_intelligence_events__event_id__memory_get': ('HTTP-0095', 'bastion_ui.transport.generated_http', 'get_event_market_memory_api_v1_intelligence_events__event_id__memory_get'),
    'get_event_market_memory_replay_api_v1_intelligence_events__event_id__memory_replay_get': ('HTTP-0097', 'bastion_ui.transport.generated_http', 'get_event_market_memory_replay_api_v1_intelligence_events__event_id__memory_replay_get'),
    'get_event_market_memory_similarity_api_v1_intelligence_events__event_id__similar_get': ('HTTP-0098', 'bastion_ui.transport.generated_http', 'get_event_market_memory_similarity_api_v1_intelligence_events__event_id__similar_get'),
    'get_event_timeline_dashboard_dto_api_v1_intelligence_events__event_id__timeline_get': ('HTTP-0099', 'bastion_ui.transport.generated_http', 'get_event_timeline_dashboard_dto_api_v1_intelligence_events__event_id__timeline_get'),
    'get_high_confidence_impacts_api_v1_intelligence_impact_high_confidence_get': ('HTTP-0100', 'bastion_ui.transport.generated_http', 'get_high_confidence_impacts_api_v1_intelligence_impact_high_confidence_get'),
    'list_narratives_api_v1_intelligence_narratives_get': ('HTTP-0101', 'bastion_ui.transport.generated_http', 'list_narratives_api_v1_intelligence_narratives_get'),
    'get_active_narrative_memory_api_v1_intelligence_narratives_active_get': ('HTTP-0102', 'bastion_ui.transport.generated_http', 'get_active_narrative_memory_api_v1_intelligence_narratives_active_get'),
    'get_narrative_dominance_api_v1_intelligence_narratives_dominance_get': ('HTTP-0103', 'bastion_ui.transport.generated_http', 'get_narrative_dominance_api_v1_intelligence_narratives_dominance_get'),
    'get_dominant_narratives_api_v1_intelligence_narratives_dominant_get': ('HTTP-0104', 'bastion_ui.transport.generated_http', 'get_dominant_narratives_api_v1_intelligence_narratives_dominant_get'),
    'get_emerging_narratives_api_v1_intelligence_narratives_emerging_get': ('HTTP-0105', 'bastion_ui.transport.generated_http', 'get_emerging_narratives_api_v1_intelligence_narratives_emerging_get'),
    'get_falling_narratives_api_v1_intelligence_narratives_falling_get': ('HTTP-0106', 'bastion_ui.transport.generated_http', 'get_falling_narratives_api_v1_intelligence_narratives_falling_get'),
    'get_narrative_heatmap_api_v1_intelligence_narratives_heatmap_get': ('HTTP-0107', 'bastion_ui.transport.generated_http', 'get_narrative_heatmap_api_v1_intelligence_narratives_heatmap_get'),
    'get_narrative_history_api_v1_intelligence_narratives_history_get': ('HTTP-0108', 'bastion_ui.transport.generated_http', 'get_narrative_history_api_v1_intelligence_narratives_history_get'),
    'get_narrative_memory_api_v1_intelligence_narratives_memory_get': ('HTTP-0109', 'bastion_ui.transport.generated_http', 'get_narrative_memory_api_v1_intelligence_narratives_memory_get'),
    'get_rising_narratives_api_v1_intelligence_narratives_rising_get': ('HTTP-0110', 'bastion_ui.transport.generated_http', 'get_rising_narratives_api_v1_intelligence_narratives_rising_get'),
    'get_narrative_rotations_api_v1_intelligence_narratives_rotations_get': ('HTTP-0111', 'bastion_ui.transport.generated_http', 'get_narrative_rotations_api_v1_intelligence_narratives_rotations_get'),
    'get_top_narratives_api_v1_intelligence_narratives_top_get': ('HTTP-0112', 'bastion_ui.transport.generated_http', 'get_top_narratives_api_v1_intelligence_narratives_top_get'),
    'get_narrative_api_v1_intelligence_narratives__slug__get': ('HTTP-0113', 'bastion_ui.transport.generated_http', 'get_narrative_api_v1_intelligence_narratives__slug__get'),
    'list_market_patterns_api_v1_intelligence_patterns_get': ('HTTP-0114', 'bastion_ui.transport.generated_http', 'list_market_patterns_api_v1_intelligence_patterns_get'),
    'get_market_pattern_api_v1_intelligence_patterns__pattern_id__get': ('HTTP-0115', 'bastion_ui.transport.generated_http', 'get_market_pattern_api_v1_intelligence_patterns__pattern_id__get'),
    'get_market_pattern_history_api_v1_intelligence_patterns__pattern_id__history_get': ('HTTP-0116', 'bastion_ui.transport.generated_http', 'get_market_pattern_history_api_v1_intelligence_patterns__pattern_id__history_get'),
    'get_market_pattern_occurrences_api_v1_intelligence_patterns__pattern_id__occurrences_get': ('HTTP-0117', 'bastion_ui.transport.generated_http', 'get_market_pattern_occurrences_api_v1_intelligence_patterns__pattern_id__occurrences_get'),
    'get_market_pattern_reaction_profile_api_v1_intelligence_patterns__pattern_id__reaction_profile_get': ('HTTP-0118', 'bastion_ui.transport.generated_http', 'get_market_pattern_reaction_profile_api_v1_intelligence_patterns__pattern_id__reaction_profile_get'),
    'get_market_pattern_statistics_api_v1_intelligence_patterns__pattern_id__statistics_get': ('HTTP-0119', 'bastion_ui.transport.generated_http', 'get_market_pattern_statistics_api_v1_intelligence_patterns__pattern_id__statistics_get'),
    'get_foundation_reaction_profile_api_v1_intelligence_reaction_profile__event_id__get': ('HTTP-0120', 'bastion_ui.transport.generated_http', 'get_foundation_reaction_profile_api_v1_intelligence_reaction_profile__event_id__get'),
    'get_foundation_similar_events_api_v1_intelligence_similar_events__event_id__get': ('HTTP-0121', 'bastion_ui.transport.generated_http', 'get_foundation_similar_events_api_v1_intelligence_similar_events__event_id__get'),
    'get_article_similarity_report_api_v1_intelligence_similarity_articles__article_id__get': ('HTTP-0122', 'bastion_ui.transport.generated_http', 'get_article_similarity_report_api_v1_intelligence_similarity_articles__article_id__get'),
    'get_candle_similarity_api_v1_intelligence_similarity_candle__candle_id__get': ('HTTP-0123', 'bastion_ui.transport.generated_http', 'get_candle_similarity_api_v1_intelligence_similarity_candle__candle_id__get'),
    'get_event_similarity_api_v1_intelligence_similarity_event__event_id__get': ('HTTP-0124', 'bastion_ui.transport.generated_http', 'get_event_similarity_api_v1_intelligence_similarity_event__event_id__get'),
    'get_event_similarity_report_api_v1_intelligence_similarity_events__event_id__get': ('HTTP-0125', 'bastion_ui.transport.generated_http', 'get_event_similarity_report_api_v1_intelligence_similarity_events__event_id__get'),
    'get_news_similarity_api_v1_intelligence_similarity_news__event_id__get': ('HTTP-0126', 'bastion_ui.transport.generated_http', 'get_news_similarity_api_v1_intelligence_similarity_news__event_id__get'),
    'get_signal_similarity_report_api_v1_intelligence_similarity_signals__signal_id__get': ('HTTP-0127', 'bastion_ui.transport.generated_http', 'get_signal_similarity_report_api_v1_intelligence_similarity_signals__signal_id__get'),
    'get_historical_similarity_context_api_v1_intelligence_similarity__event_id__get': ('HTTP-0128', 'bastion_ui.transport.generated_http', 'get_historical_similarity_context_api_v1_intelligence_similarity__event_id__get'),
    'get_historical_similarity_matches_api_v1_intelligence_similarity__event_id__matches_get': ('HTTP-0129', 'bastion_ui.transport.generated_http', 'get_historical_similarity_matches_api_v1_intelligence_similarity__event_id__matches_get'),
    'get_timeline_api_v1_intelligence_timeline_get': ('HTTP-0130', 'bastion_ui.transport.generated_http', 'get_timeline_api_v1_intelligence_timeline_get'),
    'get_context_api_v1_intelligence_timeline_context__timeline_event_id__get': ('HTTP-0131', 'bastion_ui.transport.generated_http', 'get_context_api_v1_intelligence_timeline_context__timeline_event_id__get'),
    'get_timeline_day_api_v1_intelligence_timeline_day_get': ('HTTP-0132', 'bastion_ui.transport.generated_http', 'get_timeline_day_api_v1_intelligence_timeline_day_get'),
    'get_timeline_hour_api_v1_intelligence_timeline_hour_get': ('HTTP-0133', 'bastion_ui.transport.generated_http', 'get_timeline_hour_api_v1_intelligence_timeline_hour_get'),
    'get_latest_api_v1_intelligence_timeline_latest_get': ('HTTP-0134', 'bastion_ui.transport.generated_http', 'get_latest_api_v1_intelligence_timeline_latest_get'),
    'current_narratives_api_v1_intelligence_timeline_narratives_current_get': ('HTTP-0135', 'bastion_ui.transport.generated_http', 'current_narratives_api_v1_intelligence_timeline_narratives_current_get'),
    'high_confidence_news_impacts_api_v1_intelligence_timeline_news_impacts_high_confidence_get': ('HTTP-0136', 'bastion_ui.transport.generated_http', 'high_confidence_news_impacts_api_v1_intelligence_timeline_news_impacts_high_confidence_get'),
    'recent_news_impacts_api_v1_intelligence_timeline_news_impacts_recent_get': ('HTTP-0137', 'bastion_ui.transport.generated_http', 'recent_news_impacts_api_v1_intelligence_timeline_news_impacts_recent_get'),
    'get_window_api_v1_intelligence_timeline_window_get': ('HTTP-0138', 'bastion_ui.transport.generated_http', 'get_window_api_v1_intelligence_timeline_window_get'),
    'candle_attribution_api_v1_market_time_machine_candle_attribution_get': ('HTTP-0142', 'bastion_ui.transport.generated_http', 'candle_attribution_api_v1_market_time_machine_candle_attribution_get'),
    'market_events_api_v1_market_time_machine_events_get': ('HTTP-0143', 'bastion_ui.transport.generated_http', 'market_events_api_v1_market_time_machine_events_get'),
    'news_impact_api_v1_market_time_machine_news_impact_get': ('HTTP-0144', 'bastion_ui.transport.generated_http', 'news_impact_api_v1_market_time_machine_news_impact_get'),
    'provider_degradation_api_v1_market_time_machine_provider_degradation_get': ('HTTP-0145', 'bastion_ui.transport.generated_http', 'provider_degradation_api_v1_market_time_machine_provider_degradation_get'),
    'reaction_windows_api_v1_market_time_machine_reaction_windows_get': ('HTTP-0146', 'bastion_ui.transport.generated_http', 'reaction_windows_api_v1_market_time_machine_reaction_windows_get'),
    'regime_transitions_api_v1_market_time_machine_regime_transitions_get': ('HTTP-0147', 'bastion_ui.transport.generated_http', 'regime_transitions_api_v1_market_time_machine_regime_transitions_get'),
    'signal_reliability_api_v1_market_time_machine_signal_reliability_get': ('HTTP-0148', 'bastion_ui.transport.generated_http', 'signal_reliability_api_v1_market_time_machine_signal_reliability_get'),
    'btc_candles_api_v1_market_btc_candles_get': ('HTTP-0149', 'bastion_ui.transport.generated_http', 'btc_candles_api_v1_market_btc_candles_get'),
    'btc_candles_latest_any_api_v1_market_btc_candles_latest_get': ('HTTP-0150', 'bastion_ui.transport.generated_http', 'btc_candles_latest_any_api_v1_market_btc_candles_latest_get'),
    'btc_candle_by_id_api_v1_market_btc_candles__candle_id__get': ('HTTP-0151', 'bastion_ui.transport.generated_http', 'btc_candle_by_id_api_v1_market_btc_candles__candle_id__get'),
    'btc_candle_evidence_api_v1_market_btc_candles__candle_id__evidence_get': ('HTTP-0152', 'bastion_ui.transport.generated_http', 'btc_candle_evidence_api_v1_market_btc_candles__candle_id__evidence_get'),
    'btc_candles_latest_api_v1_market_btc_candles__timeframe__latest_get': ('HTTP-0153', 'bastion_ui.transport.generated_http', 'btc_candles_latest_api_v1_market_btc_candles__timeframe__latest_get'),
    'btc_context_api_v1_market_btc_context_get': ('HTTP-0154', 'bastion_ui.transport.generated_http', 'btc_context_api_v1_market_btc_context_get'),
    'btc_price_api_v1_market_btc_price_get': ('HTTP-0155', 'bastion_ui.transport.generated_http', 'btc_price_api_v1_market_btc_price_get'),
    'btc_price_history_api_v1_market_btc_price_history_get': ('HTTP-0156', 'bastion_ui.transport.generated_http', 'btc_price_history_api_v1_market_btc_price_history_get'),
    'btc_providers_api_v1_market_btc_providers_get': ('HTTP-0157', 'bastion_ui.transport.generated_http', 'btc_providers_api_v1_market_btc_providers_get'),
    'btc_providers_health_api_v1_market_btc_providers_health_get': ('HTTP-0158', 'bastion_ui.transport.generated_http', 'btc_providers_health_api_v1_market_btc_providers_health_get'),
    'market_health_api_v1_market_health_get': ('HTTP-0159', 'bastion_ui.transport.generated_http', 'market_health_api_v1_market_health_get'),
    'providers_health_api_v1_market_providers_health_get': ('HTTP-0160', 'bastion_ui.transport.generated_http', 'providers_health_api_v1_market_providers_health_get'),
    'article_duplicates_api_v1_news_articles__article_id__duplicates_get': ('HTTP-0167', 'bastion_ui.transport.generated_http', 'article_duplicates_api_v1_news_articles__article_id__duplicates_get'),
    'by_sentiment_api_v1_news_by_sentiment__label__get': ('HTTP-0168', 'bastion_ui.transport.generated_http', 'by_sentiment_api_v1_news_by_sentiment__label__get'),
    'list_clusters_api_v1_news_clusters_get': ('HTTP-0169', 'bastion_ui.transport.generated_http', 'list_clusters_api_v1_news_clusters_get'),
    'get_cluster_api_v1_news_clusters__cluster_id__get': ('HTTP-0170', 'bastion_ui.transport.generated_http', 'get_cluster_api_v1_news_clusters__cluster_id__get'),
    'list_events_api_v1_news_events_get': ('HTTP-0171', 'bastion_ui.transport.generated_http', 'list_events_api_v1_news_events_get'),
    'high_impact_events_api_v1_news_events_high_impact_get': ('HTTP-0172', 'bastion_ui.transport.generated_http', 'high_impact_events_api_v1_news_events_high_impact_get'),
    'regulatory_events_api_v1_news_events_regulatory_get': ('HTTP-0173', 'bastion_ui.transport.generated_http', 'regulatory_events_api_v1_news_events_regulatory_get'),
    'security_events_api_v1_news_events_security_get': ('HTTP-0174', 'bastion_ui.transport.generated_http', 'security_events_api_v1_news_events_security_get'),
    'get_event_api_v1_news_events__event_id__get': ('HTTP-0175', 'bastion_ui.transport.generated_http', 'get_event_api_v1_news_events__event_id__get'),
    'get_event_articles_api_v1_news_events__event_id__articles_get': ('HTTP-0176', 'bastion_ui.transport.generated_http', 'get_event_articles_api_v1_news_events__event_id__articles_get'),
    'get_event_impact_api_v1_news_events__event_id__impact_get': ('HTTP-0177', 'bastion_ui.transport.generated_http', 'get_event_impact_api_v1_news_events__event_id__impact_get'),
    'get_event_score_api_v1_news_events__event_id__score_get': ('HTTP-0178', 'bastion_ui.transport.generated_http', 'get_event_score_api_v1_news_events__event_id__score_get'),
    'high_impact_news_api_v1_news_high_impact_get': ('HTTP-0179', 'bastion_ui.transport.generated_http', 'high_impact_news_api_v1_news_high_impact_get'),
    'high_relevance_api_v1_news_high_relevance_get': ('HTTP-0180', 'bastion_ui.transport.generated_http', 'high_relevance_api_v1_news_high_relevance_get'),
    'latest_news_api_v1_news_latest_get': ('HTTP-0181', 'bastion_ui.transport.generated_http', 'latest_news_api_v1_news_latest_get'),
    'regulatory_news_api_v1_news_regulatory_get': ('HTTP-0182', 'bastion_ui.transport.generated_http', 'regulatory_news_api_v1_news_regulatory_get'),
    'security_news_api_v1_news_security_get': ('HTTP-0183', 'bastion_ui.transport.generated_http', 'security_news_api_v1_news_security_get'),
    'list_sources_api_v1_news_sources_get': ('HTTP-0184', 'bastion_ui.transport.generated_http', 'list_sources_api_v1_news_sources_get'),
    'categories_api_v1_news_sources_categories_get': ('HTTP-0185', 'bastion_ui.transport.generated_http', 'categories_api_v1_news_sources_categories_get'),
    'sources_health_api_v1_news_sources_health_get': ('HTTP-0186', 'bastion_ui.transport.generated_http', 'sources_health_api_v1_news_sources_health_get'),
    'list_source_reputation_api_v1_news_sources_reputation_get': ('HTTP-0187', 'bastion_ui.transport.generated_http', 'list_source_reputation_api_v1_news_sources_reputation_get'),
    'tiers_api_v1_news_sources_tiers_get': ('HTTP-0189', 'bastion_ui.transport.generated_http', 'tiers_api_v1_news_sources_tiers_get'),
    'get_source_api_v1_news_sources__source_id__get': ('HTTP-0190', 'bastion_ui.transport.generated_http', 'get_source_api_v1_news_sources__source_id__get'),
    'source_confidence_events_api_v1_news_sources__source_id__confidence_events_get': ('HTTP-0191', 'bastion_ui.transport.generated_http', 'source_confidence_events_api_v1_news_sources__source_id__confidence_events_get'),
    'source_health_api_v1_news_sources__source_id__health_get': ('HTTP-0192', 'bastion_ui.transport.generated_http', 'source_health_api_v1_news_sources__source_id__health_get'),
    'source_snapshots_api_v1_news_sources__source_id__snapshots_get': ('HTTP-0193', 'bastion_ui.transport.generated_http', 'source_snapshots_api_v1_news_sources__source_id__snapshots_get'),
    'get_article_explanation_api_v1_news__article_id__explanation_get': ('HTTP-0194', 'bastion_ui.transport.generated_http', 'get_article_explanation_api_v1_news__article_id__explanation_get'),
    'get_article_impact_api_v1_news__article_id__impact_get': ('HTTP-0195', 'bastion_ui.transport.generated_http', 'get_article_impact_api_v1_news__article_id__impact_get'),
    'get_article_narratives_api_v1_news__article_id__narratives_get': ('HTTP-0196', 'bastion_ui.transport.generated_http', 'get_article_narratives_api_v1_news__article_id__narratives_get'),
    'get_article_score_api_v1_news__article_id__score_get': ('HTTP-0197', 'bastion_ui.transport.generated_http', 'get_article_score_api_v1_news__article_id__score_get'),
    'get_article_scores_api_v1_news__article_id__scores_get': ('HTTP-0198', 'bastion_ui.transport.generated_http', 'get_article_scores_api_v1_news__article_id__scores_get'),
    'onchain_events_api_v1_onchain_events_get': ('HTTP-0200', 'bastion_ui.transport.generated_http', 'onchain_events_api_v1_onchain_events_get'),
    'onchain_state_api_v1_onchain_state_get': ('HTTP-0201', 'bastion_ui.transport.generated_http', 'onchain_state_api_v1_onchain_state_get'),
    'public_features_api_v1_public_features_get': ('HTTP-0246', 'bastion_ui.transport.generated_http', 'public_features_api_v1_public_features_get'),
    'public_landing_api_v1_public_landing_get': ('HTTP-0247', 'bastion_ui.transport.generated_http', 'public_landing_api_v1_public_landing_get'),
    'public_roadmap_api_v1_public_roadmap_get': ('HTTP-0248', 'bastion_ui.transport.generated_http', 'public_roadmap_api_v1_public_roadmap_get'),
    'public_stats_api_v1_public_stats_get': ('HTTP-0249', 'bastion_ui.transport.generated_http', 'public_stats_api_v1_public_stats_get'),
    'public_status_api_v1_public_status_get': ('HTTP-0250', 'bastion_ui.transport.generated_http', 'public_status_api_v1_public_status_get'),
    'public_trace_summary_api_v1_public_trace__report_id__summary_get': ('HTTP-0251', 'bastion_ui.transport.generated_http', 'public_trace_summary_api_v1_public_trace__report_id__summary_get'),
    'latest_signals_api_v1_signals_latest_get': ('HTTP-0252', 'bastion_ui.transport.generated_http', 'latest_signals_api_v1_signals_latest_get'),
    'news_market_impact_signals_api_v1_signals_news_market_impact_get': ('HTTP-0253', 'bastion_ui.transport.generated_http', 'news_market_impact_signals_api_v1_signals_news_market_impact_get'),
    'top_signals_api_v1_signals_top_get': ('HTTP-0254', 'bastion_ui.transport.generated_http', 'top_signals_api_v1_signals_top_get'),
    'get_signal_api_v1_signals__signal_id__get': ('HTTP-0255', 'bastion_ui.transport.generated_http', 'get_signal_api_v1_signals__signal_id__get'),
    'get_signal_delivery_logs_api_v1_signals__signal_id__delivery_logs_get': ('HTTP-0256', 'bastion_ui.transport.generated_http', 'get_signal_delivery_logs_api_v1_signals__signal_id__delivery_logs_get'),
    'get_signal_evidence_api_v1_signals__signal_id__evidence_get': ('HTTP-0257', 'bastion_ui.transport.generated_http', 'get_signal_evidence_api_v1_signals__signal_id__evidence_get'),
    'signal_explanation_api_v1_signals__signal_id__explanation_get': ('HTTP-0258', 'bastion_ui.transport.generated_http', 'signal_explanation_api_v1_signals__signal_id__explanation_get'),
    'signal_recommendations_api_v1_signals__signal_id__recommendations_get': ('HTTP-0259', 'bastion_ui.transport.generated_http', 'signal_recommendations_api_v1_signals__signal_id__recommendations_get'),
    'storage_status_api_v1_storage_status_get': ('HTTP-0260', 'bastion_ui.transport.generated_http', 'storage_status_api_v1_storage_status_get'),
    'timescale_operations_status_api_v1_storage_timescale_status_get': ('HTTP-0261', 'bastion_ui.transport.generated_http', 'timescale_operations_status_api_v1_storage_timescale_status_get'),
    'analyze_address_api_v1_trace_address__address__get': ('HTTP-0262', 'bastion_ui.transport.generated_http', 'analyze_address_api_v1_trace_address__address__get'),
    'trace_alerts_api_v1_trace_alerts_get': ('HTTP-0263', 'bastion_ui.transport.generated_http', 'trace_alerts_api_v1_trace_alerts_get'),
    'trace_events_api_v1_trace_events_get': ('HTTP-0276', 'bastion_ui.transport.generated_http', 'trace_events_api_v1_trace_events_get'),
    'trace_event_api_v1_trace_events__event_id__get': ('HTTP-0277', 'bastion_ui.transport.generated_http', 'trace_event_api_v1_trace_events__event_id__get'),
    'lite_address_check_api_v1_trace_lite__address__get': ('HTTP-0278', 'bastion_ui.transport.generated_http', 'lite_address_check_api_v1_trace_lite__address__get'),
    'get_report_api_v1_trace_report__report_id__get': ('HTTP-0282', 'bastion_ui.transport.generated_http', 'get_report_api_v1_trace_report__report_id__get'),
    'trace_citadel_contribution_api_v1_trace_report__report_id__citadel_contribution_get': ('HTTP-0283', 'bastion_ui.transport.generated_http', 'trace_citadel_contribution_api_v1_trace_report__report_id__citadel_contribution_get'),
    'get_counterparty_lens_api_v1_trace_report__report_id__counterparty_lens_get': ('HTTP-0284', 'bastion_ui.transport.generated_http', 'get_counterparty_lens_api_v1_trace_report__report_id__counterparty_lens_get'),
    'get_dust_radar_api_v1_trace_report__report_id__dust_radar_get': ('HTTP-0285', 'bastion_ui.transport.generated_http', 'get_dust_radar_api_v1_trace_report__report_id__dust_radar_get'),
    'list_evidence_api_v1_trace_report__report_id__evidence_get': ('HTTP-0286', 'bastion_ui.transport.generated_http', 'list_evidence_api_v1_trace_report__report_id__evidence_get'),
    'trace_evidence_refs_api_v1_trace_report__report_id__evidence_refs_get': ('HTTP-0287', 'bastion_ui.transport.generated_http', 'trace_evidence_refs_api_v1_trace_report__report_id__evidence_refs_get'),
    'get_origin_passport_api_v1_trace_report__report_id__origin_passport_get': ('HTTP-0288', 'bastion_ui.transport.generated_http', 'get_origin_passport_api_v1_trace_report__report_id__origin_passport_get'),
    'trace_policy_facts_api_v1_trace_report__report_id__policy_facts_get': ('HTTP-0289', 'bastion_ui.transport.generated_http', 'trace_policy_facts_api_v1_trace_report__report_id__policy_facts_get'),
    'get_privacy_shield_api_v1_trace_report__report_id__privacy_shield_get': ('HTTP-0290', 'bastion_ui.transport.generated_http', 'get_privacy_shield_api_v1_trace_report__report_id__privacy_shield_get'),
    'get_proof_packet_api_v1_trace_report__report_id__proof_packet_get': ('HTTP-0291', 'bastion_ui.transport.generated_http', 'get_proof_packet_api_v1_trace_report__report_id__proof_packet_get'),
    'get_provider_disagreement_api_v1_trace_report__report_id__provider_disagreement_get': ('HTTP-0292', 'bastion_ui.transport.generated_http', 'get_provider_disagreement_api_v1_trace_report__report_id__provider_disagreement_get'),
    'get_source_summary_api_v1_trace_report__report_id__source_summary_get': ('HTTP-0293', 'bastion_ui.transport.generated_http', 'get_source_summary_api_v1_trace_report__report_id__source_summary_get'),
    'get_utxo_hygiene_api_v1_trace_report__report_id__utxo_hygiene_get': ('HTTP-0294', 'bastion_ui.transport.generated_http', 'get_utxo_hygiene_api_v1_trace_report__report_id__utxo_hygiene_get'),
    'list_sources_api_v1_trace_sources_get': ('HTTP-0295', 'bastion_ui.transport.generated_http', 'list_sources_api_v1_trace_sources_get'),
    'get_source_api_v1_trace_sources__source_name__get': ('HTTP-0296', 'bastion_ui.transport.generated_http', 'get_source_api_v1_trace_sources__source_name__get'),
    'trace_status_api_v1_trace_status_get': ('HTTP-0297', 'bastion_ui.transport.generated_http', 'trace_status_api_v1_trace_status_get'),
    'list_watchlist_api_v1_trace_watchlist_get': ('HTTP-0299', 'bastion_ui.transport.generated_http', 'list_watchlist_api_v1_trace_watchlist_get'),
    'dependencies_health_dependencies_get': ('HTTP-0341', 'bastion_ui.transport.generated_http', 'dependencies_health_dependencies_get'),
    'intelligence_health_intelligence_get': ('HTTP-0342', 'bastion_ui.transport.generated_http', 'intelligence_health_intelligence_get'),
    'live_health_live_get': ('HTTP-0343', 'bastion_ui.transport.generated_http', 'live_health_live_get'),
    'operations_health_operations_get': ('HTTP-0344', 'bastion_ui.transport.generated_http', 'operations_health_operations_get'),
    'providers_health_providers_get': ('HTTP-0345', 'bastion_ui.transport.generated_http', 'providers_health_providers_get'),
    'ready_health_ready_get': ('HTTP-0346', 'bastion_ui.transport.generated_http', 'ready_health_ready_get'),
    'startup_health_startup_get': ('HTTP-0347', 'bastion_ui.transport.generated_http', 'startup_health_startup_get'),
    'web_candle_dto_web_candle__candle_id__get': ('HTTP-0362', 'bastion_ui.transport.generated_http', 'web_candle_dto_web_candle__candle_id__get'),
    'web_evidence_dto_web_evidence__packet_id__get': ('HTTP-0363', 'bastion_ui.transport.generated_http', 'web_evidence_dto_web_evidence__packet_id__get'),
    'web_market_time_machine_dto_web_market_time_machine_get': ('HTTP-0364', 'bastion_ui.transport.generated_http', 'web_market_time_machine_dto_web_market_time_machine_get'),
    'web_timeline_dto_web_timeline_get': ('HTTP-0369', 'bastion_ui.transport.generated_http', 'web_timeline_dto_web_timeline_get'),
}

FEATURE_53 = (
    ContractRegistryEntry(registry_id='http:list_child_api_keys_api_v1_access_api_keys_get', source_head=SOURCE_HEAD, operation=LISTCHILDAPIKEYSAPIV1ACCESSAPIKEYSGET_OPERATION, request_schema='ListChildApiKeysApiV1AccessApiKeysGetRequest', success_schema='ListChildApiKeysApiV1AccessApiKeysGetSuccess', error_schema='ListChildApiKeysApiV1AccessApiKeysGetError'),
    ContractRegistryEntry(registry_id='http:get_child_api_key_api_v1_access_api_keys__key_id__get', source_head=SOURCE_HEAD, operation=GETCHILDAPIKEYAPIV1ACCESSAPIKEYSKEYIDGET_OPERATION, request_schema='GetChildApiKeyApiV1AccessApiKeysKeyIdGetRequest', success_schema='GetChildApiKeyApiV1AccessApiKeysKeyIdGetSuccess', error_schema='GetChildApiKeyApiV1AccessApiKeysKeyIdGetError'),
    ContractRegistryEntry(registry_id='http:list_delegated_passes_api_v1_access_delegated_passes_get', source_head=SOURCE_HEAD, operation=LISTDELEGATEDPASSESAPIV1ACCESSDELEGATEDPASSESGET_OPERATION, request_schema='ListDelegatedPassesApiV1AccessDelegatedPassesGetRequest', success_schema='ListDelegatedPassesApiV1AccessDelegatedPassesGetSuccess', error_schema='ListDelegatedPassesApiV1AccessDelegatedPassesGetError'),
    ContractRegistryEntry(registry_id='http:get_delegated_pass_api_v1_access_delegated_passes__delegated_pass_id__get', source_head=SOURCE_HEAD, operation=GETDELEGATEDPASSAPIV1ACCESSDELEGATEDPASSESDELEGATEDPASSIDGET_OPERATION, request_schema='GetDelegatedPassApiV1AccessDelegatedPassesDelegatedPassIdGetRequest', success_schema='GetDelegatedPassApiV1AccessDelegatedPassesDelegatedPassIdGetSuccess', error_schema='GetDelegatedPassApiV1AccessDelegatedPassesDelegatedPassIdGetError'),
    ContractRegistryEntry(registry_id='http:get_human_intent_api_v1_access_intents__intent_id__get', source_head=SOURCE_HEAD, operation=GETHUMANINTENTAPIV1ACCESSINTENTSINTENTIDGET_OPERATION, request_schema='GetHumanIntentApiV1AccessIntentsIntentIdGetRequest', success_schema='GetHumanIntentApiV1AccessIntentsIntentIdGetSuccess', error_schema='GetHumanIntentApiV1AccessIntentsIntentIdGetError'),
    ContractRegistryEntry(registry_id='http:get_me_api_v1_access_me_get', source_head=SOURCE_HEAD, operation=GETMEAPIV1ACCESSMEGET_OPERATION, request_schema='GetMeApiV1AccessMeGetRequest', success_schema='GetMeApiV1AccessMeGetSuccess', error_schema='GetMeApiV1AccessMeGetError'),
    ContractRegistryEntry(registry_id='http:get_my_entitlements_api_v1_access_me_entitlements_get', source_head=SOURCE_HEAD, operation=GETMYENTITLEMENTSAPIV1ACCESSMEENTITLEMENTSGET_OPERATION, request_schema='GetMyEntitlementsApiV1AccessMeEntitlementsGetRequest', success_schema='GetMyEntitlementsApiV1AccessMeEntitlementsGetSuccess', error_schema='GetMyEntitlementsApiV1AccessMeEntitlementsGetError'),
    ContractRegistryEntry(registry_id='http:get_my_limits_api_v1_access_me_limits_get', source_head=SOURCE_HEAD, operation=GETMYLIMITSAPIV1ACCESSMELIMITSGET_OPERATION, request_schema='GetMyLimitsApiV1AccessMeLimitsGetRequest', success_schema='GetMyLimitsApiV1AccessMeLimitsGetSuccess', error_schema='GetMyLimitsApiV1AccessMeLimitsGetError'),
    ContractRegistryEntry(registry_id='http:get_payment_intent_status_api_v1_access_payment_intents__payment_intent_id__get', source_head=SOURCE_HEAD, operation=GETPAYMENTINTENTSTATUSAPIV1ACCESSPAYMENTINTENTSPAYMENTINTENTIDGET_OPERATION, request_schema='GetPaymentIntentStatusApiV1AccessPaymentIntentsPaymentIntentIdGetRequest', success_schema='GetPaymentIntentStatusApiV1AccessPaymentIntentsPaymentIntentIdGetSuccess', error_schema='GetPaymentIntentStatusApiV1AccessPaymentIntentsPaymentIntentIdGetError'),
    ContractRegistryEntry(registry_id='http:recovery_status_api_v1_access_recovery_status__recovery_attempt_id__get', source_head=SOURCE_HEAD, operation=RECOVERYSTATUSAPIV1ACCESSRECOVERYSTATUSRECOVERYATTEMPTIDGET_OPERATION, request_schema='RecoveryStatusApiV1AccessRecoveryStatusRecoveryAttemptIdGetRequest', success_schema='RecoveryStatusApiV1AccessRecoveryStatusRecoveryAttemptIdGetSuccess', error_schema='RecoveryStatusApiV1AccessRecoveryStatusRecoveryAttemptIdGetError'),
    ContractRegistryEntry(registry_id='http:list_addresses_api_v1_business_lightning_addresses_get', source_head=SOURCE_HEAD, operation=LISTADDRESSESAPIV1BUSINESSLIGHTNINGADDRESSESGET_OPERATION, request_schema='ListAddressesApiV1BusinessLightningAddressesGetRequest', success_schema='ListAddressesApiV1BusinessLightningAddressesGetSuccess', error_schema='ListAddressesApiV1BusinessLightningAddressesGetError'),
    ContractRegistryEntry(registry_id='http:get_address_api_v1_business_lightning_addresses__address_id__get', source_head=SOURCE_HEAD, operation=GETADDRESSAPIV1BUSINESSLIGHTNINGADDRESSESADDRESSIDGET_OPERATION, request_schema='GetAddressApiV1BusinessLightningAddressesAddressIdGetRequest', success_schema='GetAddressApiV1BusinessLightningAddressesAddressIdGetSuccess', error_schema='GetAddressApiV1BusinessLightningAddressesAddressIdGetError'),
    ContractRegistryEntry(registry_id='http:list_domains_api_v1_business_lightning_domains_get', source_head=SOURCE_HEAD, operation=LISTDOMAINSAPIV1BUSINESSLIGHTNINGDOMAINSGET_OPERATION, request_schema='ListDomainsApiV1BusinessLightningDomainsGetRequest', success_schema='ListDomainsApiV1BusinessLightningDomainsGetSuccess', error_schema='ListDomainsApiV1BusinessLightningDomainsGetError'),
    ContractRegistryEntry(registry_id='http:get_domain_api_v1_business_lightning_domains__domain_id__get', source_head=SOURCE_HEAD, operation=GETDOMAINAPIV1BUSINESSLIGHTNINGDOMAINSDOMAINIDGET_OPERATION, request_schema='GetDomainApiV1BusinessLightningDomainsDomainIdGetRequest', success_schema='GetDomainApiV1BusinessLightningDomainsDomainIdGetSuccess', error_schema='GetDomainApiV1BusinessLightningDomainsDomainIdGetError'),
    ContractRegistryEntry(registry_id='http:citadel_assessment_api_v1_citadel_assessment_get', source_head=SOURCE_HEAD, operation=CITADELASSESSMENTAPIV1CITADELASSESSMENTGET_OPERATION, request_schema='CitadelAssessmentApiV1CitadelAssessmentGetRequest', success_schema='CitadelAssessmentApiV1CitadelAssessmentGetSuccess', error_schema='CitadelAssessmentApiV1CitadelAssessmentGetError'),
    ContractRegistryEntry(registry_id='http:citadel_dependencies_api_v1_citadel_dependencies_get', source_head=SOURCE_HEAD, operation=CITADELDEPENDENCIESAPIV1CITADELDEPENDENCIESGET_OPERATION, request_schema='CitadelDependenciesApiV1CitadelDependenciesGetRequest', success_schema='CitadelDependenciesApiV1CitadelDependenciesGetSuccess', error_schema='CitadelDependenciesApiV1CitadelDependenciesGetError'),
    ContractRegistryEntry(registry_id='http:citadel_inheritance_api_v1_citadel_inheritance_get', source_head=SOURCE_HEAD, operation=CITADELINHERITANCEAPIV1CITADELINHERITANCEGET_OPERATION, request_schema='CitadelInheritanceApiV1CitadelInheritanceGetRequest', success_schema='CitadelInheritanceApiV1CitadelInheritanceGetSuccess', error_schema='CitadelInheritanceApiV1CitadelInheritanceGetError'),
    ContractRegistryEntry(registry_id='http:citadel_overview_api_v1_citadel_overview_get', source_head=SOURCE_HEAD, operation=CITADELOVERVIEWAPIV1CITADELOVERVIEWGET_OPERATION, request_schema='CitadelOverviewApiV1CitadelOverviewGetRequest', success_schema='CitadelOverviewApiV1CitadelOverviewGetSuccess', error_schema='CitadelOverviewApiV1CitadelOverviewGetError'),
    ContractRegistryEntry(registry_id='http:citadel_policy_checks_api_v1_citadel_policy_checks_get', source_head=SOURCE_HEAD, operation=CITADELPOLICYCHECKSAPIV1CITADELPOLICYCHECKSGET_OPERATION, request_schema='CitadelPolicyChecksApiV1CitadelPolicyChecksGetRequest', success_schema='CitadelPolicyChecksApiV1CitadelPolicyChecksGetSuccess', error_schema='CitadelPolicyChecksApiV1CitadelPolicyChecksGetError'),
    ContractRegistryEntry(registry_id='http:citadel_recovery_api_v1_citadel_recovery_get', source_head=SOURCE_HEAD, operation=CITADELRECOVERYAPIV1CITADELRECOVERYGET_OPERATION, request_schema='CitadelRecoveryApiV1CitadelRecoveryGetRequest', success_schema='CitadelRecoveryApiV1CitadelRecoveryGetSuccess', error_schema='CitadelRecoveryApiV1CitadelRecoveryGetError'),
    ContractRegistryEntry(registry_id='http:citadel_repair_plan_api_v1_citadel_repair_plan_get', source_head=SOURCE_HEAD, operation=CITADELREPAIRPLANAPIV1CITADELREPAIRPLANGET_OPERATION, request_schema='CitadelRepairPlanApiV1CitadelRepairPlanGetRequest', success_schema='CitadelRepairPlanApiV1CitadelRepairPlanGetSuccess', error_schema='CitadelRepairPlanApiV1CitadelRepairPlanGetError'),
    ContractRegistryEntry(registry_id='http:list_simulations_api_v1_citadel_simulations_get', source_head=SOURCE_HEAD, operation=LISTSIMULATIONSAPIV1CITADELSIMULATIONSGET_OPERATION, request_schema='ListSimulationsApiV1CitadelSimulationsGetRequest', success_schema='ListSimulationsApiV1CitadelSimulationsGetSuccess', error_schema='ListSimulationsApiV1CitadelSimulationsGetError'),
    ContractRegistryEntry(registry_id='http:list_snippets_api_v1_education_snippets_get', source_head=SOURCE_HEAD, operation=LISTSNIPPETSAPIV1EDUCATIONSNIPPETSGET_OPERATION, request_schema='ListSnippetsApiV1EducationSnippetsGetRequest', success_schema='ListSnippetsApiV1EducationSnippetsGetSuccess', error_schema='ListSnippetsApiV1EducationSnippetsGetError'),
    ContractRegistryEntry(registry_id='http:list_entities_api_v1_entities_get', source_head=SOURCE_HEAD, operation=LISTENTITIESAPIV1ENTITIESGET_OPERATION, request_schema='ListEntitiesApiV1EntitiesGetRequest', success_schema='ListEntitiesApiV1EntitiesGetSuccess', error_schema='ListEntitiesApiV1EntitiesGetError'),
    ContractRegistryEntry(registry_id='http:get_market_memory_evidence_api_v1_evidence_market_memory__event_id__get', source_head=SOURCE_HEAD, operation=GETMARKETMEMORYEVIDENCEAPIV1EVIDENCEMARKETMEMORYEVENTIDGET_OPERATION, request_schema='GetMarketMemoryEvidenceApiV1EvidenceMarketMemoryEventIdGetRequest', success_schema='GetMarketMemoryEvidenceApiV1EvidenceMarketMemoryEventIdGetSuccess', error_schema='GetMarketMemoryEvidenceApiV1EvidenceMarketMemoryEventIdGetError'),
    ContractRegistryEntry(registry_id='http:list_evidence_packets_api_v1_evidence_packets_get', source_head=SOURCE_HEAD, operation=LISTEVIDENCEPACKETSAPIV1EVIDENCEPACKETSGET_OPERATION, request_schema='ListEvidencePacketsApiV1EvidencePacketsGetRequest', success_schema='ListEvidencePacketsApiV1EvidencePacketsGetSuccess', error_schema='ListEvidencePacketsApiV1EvidencePacketsGetError'),
    ContractRegistryEntry(registry_id='http:get_evidence_packet_api_v1_evidence_packets__packet_id__get', source_head=SOURCE_HEAD, operation=GETEVIDENCEPACKETAPIV1EVIDENCEPACKETSPACKETIDGET_OPERATION, request_schema='GetEvidencePacketApiV1EvidencePacketsPacketIdGetRequest', success_schema='GetEvidencePacketApiV1EvidencePacketsPacketIdGetSuccess', error_schema='GetEvidencePacketApiV1EvidencePacketsPacketIdGetError'),
    ContractRegistryEntry(registry_id='http:get_evidence_packet_relationships_api_v1_evidence_packets__packet_id__relationships_get', source_head=SOURCE_HEAD, operation=GETEVIDENCEPACKETRELATIONSHIPSAPIV1EVIDENCEPACKETSPACKETIDRELATIONSHIPSGET_OPERATION, request_schema='GetEvidencePacketRelationshipsApiV1EvidencePacketsPacketIdRelationshipsGetRequest', success_schema='GetEvidencePacketRelationshipsApiV1EvidencePacketsPacketIdRelationshipsGetSuccess', error_schema='GetEvidencePacketRelationshipsApiV1EvidencePacketsPacketIdRelationshipsGetError'),
    ContractRegistryEntry(registry_id='http:get_evidence_packet_timeline_api_v1_evidence_packets__packet_id__timeline_get', source_head=SOURCE_HEAD, operation=GETEVIDENCEPACKETTIMELINEAPIV1EVIDENCEPACKETSPACKETIDTIMELINEGET_OPERATION, request_schema='GetEvidencePacketTimelineApiV1EvidencePacketsPacketIdTimelineGetRequest', success_schema='GetEvidencePacketTimelineApiV1EvidencePacketsPacketIdTimelineGetSuccess', error_schema='GetEvidencePacketTimelineApiV1EvidencePacketsPacketIdTimelineGetError'),
    ContractRegistryEntry(registry_id='http:replay_evidence_api_v1_evidence_replay__entity_type___entity_id__get', source_head=SOURCE_HEAD, operation=REPLAYEVIDENCEAPIV1EVIDENCEREPLAYENTITYTYPEENTITYIDGET_OPERATION, request_schema='ReplayEvidenceApiV1EvidenceReplayEntityTypeEntityIdGetRequest', success_schema='ReplayEvidenceApiV1EvidenceReplayEntityTypeEntityIdGetSuccess', error_schema='ReplayEvidenceApiV1EvidenceReplayEntityTypeEntityIdGetError'),
    ContractRegistryEntry(registry_id='http:replay_evidence_integrity_api_v1_evidence_replay__entity_type___entity_id__integrity_get', source_head=SOURCE_HEAD, operation=REPLAYEVIDENCEINTEGRITYAPIV1EVIDENCEREPLAYENTITYTYPEENTITYIDINTEGRITYGET_OPERATION, request_schema='ReplayEvidenceIntegrityApiV1EvidenceReplayEntityTypeEntityIdIntegrityGetRequest', success_schema='ReplayEvidenceIntegrityApiV1EvidenceReplayEntityTypeEntityIdIntegrityGetSuccess', error_schema='ReplayEvidenceIntegrityApiV1EvidenceReplayEntityTypeEntityIdIntegrityGetError'),
    ContractRegistryEntry(registry_id='http:replay_evidence_timeline_api_v1_evidence_replay__entity_type___entity_id__timeline_get', source_head=SOURCE_HEAD, operation=REPLAYEVIDENCETIMELINEAPIV1EVIDENCEREPLAYENTITYTYPEENTITYIDTIMELINEGET_OPERATION, request_schema='ReplayEvidenceTimelineApiV1EvidenceReplayEntityTypeEntityIdTimelineGetRequest', success_schema='ReplayEvidenceTimelineApiV1EvidenceReplayEntityTypeEntityIdTimelineGetSuccess', error_schema='ReplayEvidenceTimelineApiV1EvidenceReplayEntityTypeEntityIdTimelineGetError'),
    ContractRegistryEntry(registry_id='http:health_api_v1_health_get', source_head=SOURCE_HEAD, operation=HEALTHAPIV1HEALTHGET_OPERATION, request_schema='HealthApiV1HealthGetRequest', success_schema='HealthApiV1HealthGetSuccess', error_schema='HealthApiV1HealthGetError'),
    ContractRegistryEntry(registry_id='http:degraded_api_v1_health_degraded_get', source_head=SOURCE_HEAD, operation=DEGRADEDAPIV1HEALTHDEGRADEDGET_OPERATION, request_schema='DegradedApiV1HealthDegradedGetRequest', success_schema='DegradedApiV1HealthDegradedGetSuccess', error_schema='DegradedApiV1HealthDegradedGetError'),
    ContractRegistryEntry(registry_id='http:jobs_api_v1_health_jobs_get', source_head=SOURCE_HEAD, operation=JOBSAPIV1HEALTHJOBSGET_OPERATION, request_schema='JobsApiV1HealthJobsGetRequest', success_schema='JobsApiV1HealthJobsGetSuccess', error_schema='JobsApiV1HealthJobsGetError'),
    ContractRegistryEntry(registry_id='http:liveness_api_v1_health_live_get', source_head=SOURCE_HEAD, operation=LIVENESSAPIV1HEALTHLIVEGET_OPERATION, request_schema='LivenessApiV1HealthLiveGetRequest', success_schema='LivenessApiV1HealthLiveGetSuccess', error_schema='LivenessApiV1HealthLiveGetError'),
    ContractRegistryEntry(registry_id='http:providers_api_v1_health_providers_get', source_head=SOURCE_HEAD, operation=PROVIDERSAPIV1HEALTHPROVIDERSGET_OPERATION, request_schema='ProvidersApiV1HealthProvidersGetRequest', success_schema='ProvidersApiV1HealthProvidersGetSuccess', error_schema='ProvidersApiV1HealthProvidersGetError'),
    ContractRegistryEntry(registry_id='http:readiness_api_v1_health_ready_get', source_head=SOURCE_HEAD, operation=READINESSAPIV1HEALTHREADYGET_OPERATION, request_schema='ReadinessApiV1HealthReadyGetRequest', success_schema='ReadinessApiV1HealthReadyGetSuccess', error_schema='ReadinessApiV1HealthReadyGetError'),
    ContractRegistryEntry(registry_id='http:runtime_api_v1_health_runtime_get', source_head=SOURCE_HEAD, operation=RUNTIMEAPIV1HEALTHRUNTIMEGET_OPERATION, request_schema='RuntimeApiV1HealthRuntimeGetRequest', success_schema='RuntimeApiV1HealthRuntimeGetSuccess', error_schema='RuntimeApiV1HealthRuntimeGetError'),
    ContractRegistryEntry(registry_id='http:system_health_api_v1_health_system_get', source_head=SOURCE_HEAD, operation=SYSTEMHEALTHAPIV1HEALTHSYSTEMGET_OPERATION, request_schema='SystemHealthApiV1HealthSystemGetRequest', success_schema='SystemHealthApiV1HealthSystemGetSuccess', error_schema='SystemHealthApiV1HealthSystemGetError'),
    ContractRegistryEntry(registry_id='http:get_candle_dashboard_dto_api_v1_intelligence_candles__candle_id__get', source_head=SOURCE_HEAD, operation=GETCANDLEDASHBOARDDTOAPIV1INTELLIGENCECANDLESCANDLEIDGET_OPERATION, request_schema='GetCandleDashboardDtoApiV1IntelligenceCandlesCandleIdGetRequest', success_schema='GetCandleDashboardDtoApiV1IntelligenceCandlesCandleIdGetSuccess', error_schema='GetCandleDashboardDtoApiV1IntelligenceCandlesCandleIdGetError'),
    ContractRegistryEntry(registry_id='http:get_candle_attribution_api_v1_intelligence_candles__candle_id__attribution_get', source_head=SOURCE_HEAD, operation=GETCANDLEATTRIBUTIONAPIV1INTELLIGENCECANDLESCANDLEIDATTRIBUTIONGET_OPERATION, request_schema='GetCandleAttributionApiV1IntelligenceCandlesCandleIdAttributionGetRequest', success_schema='GetCandleAttributionApiV1IntelligenceCandlesCandleIdAttributionGetSuccess', error_schema='GetCandleAttributionApiV1IntelligenceCandlesCandleIdAttributionGetError'),
    ContractRegistryEntry(registry_id='http:get_candle_candidates_api_v1_intelligence_candles__candle_id__candidates_get', source_head=SOURCE_HEAD, operation=GETCANDLECANDIDATESAPIV1INTELLIGENCECANDLESCANDLEIDCANDIDATESGET_OPERATION, request_schema='GetCandleCandidatesApiV1IntelligenceCandlesCandleIdCandidatesGetRequest', success_schema='GetCandleCandidatesApiV1IntelligenceCandlesCandleIdCandidatesGetSuccess', error_schema='GetCandleCandidatesApiV1IntelligenceCandlesCandleIdCandidatesGetError'),
    ContractRegistryEntry(registry_id='http:get_candle_context_api_v1_intelligence_candles__candle_id__context_get', source_head=SOURCE_HEAD, operation=GETCANDLECONTEXTAPIV1INTELLIGENCECANDLESCANDLEIDCONTEXTGET_OPERATION, request_schema='GetCandleContextApiV1IntelligenceCandlesCandleIdContextGetRequest', success_schema='GetCandleContextApiV1IntelligenceCandlesCandleIdContextGetSuccess', error_schema='GetCandleContextApiV1IntelligenceCandlesCandleIdContextGetError'),
    ContractRegistryEntry(registry_id='http:get_candle_events_dashboard_dto_api_v1_intelligence_candles__candle_id__events_get', source_head=SOURCE_HEAD, operation=GETCANDLEEVENTSDASHBOARDDTOAPIV1INTELLIGENCECANDLESCANDLEIDEVENTSGET_OPERATION, request_schema='GetCandleEventsDashboardDtoApiV1IntelligenceCandlesCandleIdEventsGetRequest', success_schema='GetCandleEventsDashboardDtoApiV1IntelligenceCandlesCandleIdEventsGetSuccess', error_schema='GetCandleEventsDashboardDtoApiV1IntelligenceCandlesCandleIdEventsGetError'),
    ContractRegistryEntry(registry_id='http:get_candle_evidence_dashboard_dto_api_v1_intelligence_candles__candle_id__evidence_get', source_head=SOURCE_HEAD, operation=GETCANDLEEVIDENCEDASHBOARDDTOAPIV1INTELLIGENCECANDLESCANDLEIDEVIDENCEGET_OPERATION, request_schema='GetCandleEvidenceDashboardDtoApiV1IntelligenceCandlesCandleIdEvidenceGetRequest', success_schema='GetCandleEvidenceDashboardDtoApiV1IntelligenceCandlesCandleIdEvidenceGetSuccess', error_schema='GetCandleEvidenceDashboardDtoApiV1IntelligenceCandlesCandleIdEvidenceGetError'),
    ContractRegistryEntry(registry_id='http:explain_candle_api_v1_intelligence_candles__candle_id__explain_get', source_head=SOURCE_HEAD, operation=EXPLAINCANDLEAPIV1INTELLIGENCECANDLESCANDLEIDEXPLAINGET_OPERATION, request_schema='ExplainCandleApiV1IntelligenceCandlesCandleIdExplainGetRequest', success_schema='ExplainCandleApiV1IntelligenceCandlesCandleIdExplainGetSuccess', error_schema='ExplainCandleApiV1IntelligenceCandlesCandleIdExplainGetError'),
    ContractRegistryEntry(registry_id='http:get_candle_replay_api_v1_intelligence_candles__candle_id__replay_get', source_head=SOURCE_HEAD, operation=GETCANDLEREPLAYAPIV1INTELLIGENCECANDLESCANDLEIDREPLAYGET_OPERATION, request_schema='GetCandleReplayApiV1IntelligenceCandlesCandleIdReplayGetRequest', success_schema='GetCandleReplayApiV1IntelligenceCandlesCandleIdReplayGetSuccess', error_schema='GetCandleReplayApiV1IntelligenceCandlesCandleIdReplayGetError'),
    ContractRegistryEntry(registry_id='http:get_candle_similarity_dashboard_dto_api_v1_intelligence_candles__candle_id__similar_get', source_head=SOURCE_HEAD, operation=GETCANDLESIMILARITYDASHBOARDDTOAPIV1INTELLIGENCECANDLESCANDLEIDSIMILARGET_OPERATION, request_schema='GetCandleSimilarityDashboardDtoApiV1IntelligenceCandlesCandleIdSimilarGetRequest', success_schema='GetCandleSimilarityDashboardDtoApiV1IntelligenceCandlesCandleIdSimilarGetSuccess', error_schema='GetCandleSimilarityDashboardDtoApiV1IntelligenceCandlesCandleIdSimilarGetError'),
    ContractRegistryEntry(registry_id='http:get_candle_top_events_api_v1_intelligence_candles__candle_id__top_events_get', source_head=SOURCE_HEAD, operation=GETCANDLETOPEVENTSAPIV1INTELLIGENCECANDLESCANDLEIDTOPEVENTSGET_OPERATION, request_schema='GetCandleTopEventsApiV1IntelligenceCandlesCandleIdTopEventsGetRequest', success_schema='GetCandleTopEventsApiV1IntelligenceCandlesCandleIdTopEventsGetSuccess', error_schema='GetCandleTopEventsApiV1IntelligenceCandlesCandleIdTopEventsGetError'),
    ContractRegistryEntry(registry_id='http:get_event_market_memory_api_v1_intelligence_events__event_id__memory_get', source_head=SOURCE_HEAD, operation=GETEVENTMARKETMEMORYAPIV1INTELLIGENCEEVENTSEVENTIDMEMORYGET_OPERATION, request_schema='GetEventMarketMemoryApiV1IntelligenceEventsEventIdMemoryGetRequest', success_schema='GetEventMarketMemoryApiV1IntelligenceEventsEventIdMemoryGetSuccess', error_schema='GetEventMarketMemoryApiV1IntelligenceEventsEventIdMemoryGetError'),
    ContractRegistryEntry(registry_id='http:get_event_market_memory_replay_api_v1_intelligence_events__event_id__memory_replay_get', source_head=SOURCE_HEAD, operation=GETEVENTMARKETMEMORYREPLAYAPIV1INTELLIGENCEEVENTSEVENTIDMEMORYREPLAYGET_OPERATION, request_schema='GetEventMarketMemoryReplayApiV1IntelligenceEventsEventIdMemoryReplayGetRequest', success_schema='GetEventMarketMemoryReplayApiV1IntelligenceEventsEventIdMemoryReplayGetSuccess', error_schema='GetEventMarketMemoryReplayApiV1IntelligenceEventsEventIdMemoryReplayGetError'),
    ContractRegistryEntry(registry_id='http:get_event_market_memory_similarity_api_v1_intelligence_events__event_id__similar_get', source_head=SOURCE_HEAD, operation=GETEVENTMARKETMEMORYSIMILARITYAPIV1INTELLIGENCEEVENTSEVENTIDSIMILARGET_OPERATION, request_schema='GetEventMarketMemorySimilarityApiV1IntelligenceEventsEventIdSimilarGetRequest', success_schema='GetEventMarketMemorySimilarityApiV1IntelligenceEventsEventIdSimilarGetSuccess', error_schema='GetEventMarketMemorySimilarityApiV1IntelligenceEventsEventIdSimilarGetError'),
    ContractRegistryEntry(registry_id='http:get_event_timeline_dashboard_dto_api_v1_intelligence_events__event_id__timeline_get', source_head=SOURCE_HEAD, operation=GETEVENTTIMELINEDASHBOARDDTOAPIV1INTELLIGENCEEVENTSEVENTIDTIMELINEGET_OPERATION, request_schema='GetEventTimelineDashboardDtoApiV1IntelligenceEventsEventIdTimelineGetRequest', success_schema='GetEventTimelineDashboardDtoApiV1IntelligenceEventsEventIdTimelineGetSuccess', error_schema='GetEventTimelineDashboardDtoApiV1IntelligenceEventsEventIdTimelineGetError'),
    ContractRegistryEntry(registry_id='http:get_high_confidence_impacts_api_v1_intelligence_impact_high_confidence_get', source_head=SOURCE_HEAD, operation=GETHIGHCONFIDENCEIMPACTSAPIV1INTELLIGENCEIMPACTHIGHCONFIDENCEGET_OPERATION, request_schema='GetHighConfidenceImpactsApiV1IntelligenceImpactHighConfidenceGetRequest', success_schema='GetHighConfidenceImpactsApiV1IntelligenceImpactHighConfidenceGetSuccess', error_schema='GetHighConfidenceImpactsApiV1IntelligenceImpactHighConfidenceGetError'),
    ContractRegistryEntry(registry_id='http:list_narratives_api_v1_intelligence_narratives_get', source_head=SOURCE_HEAD, operation=LISTNARRATIVESAPIV1INTELLIGENCENARRATIVESGET_OPERATION, request_schema='ListNarrativesApiV1IntelligenceNarrativesGetRequest', success_schema='ListNarrativesApiV1IntelligenceNarrativesGetSuccess', error_schema='ListNarrativesApiV1IntelligenceNarrativesGetError'),
    ContractRegistryEntry(registry_id='http:get_active_narrative_memory_api_v1_intelligence_narratives_active_get', source_head=SOURCE_HEAD, operation=GETACTIVENARRATIVEMEMORYAPIV1INTELLIGENCENARRATIVESACTIVEGET_OPERATION, request_schema='GetActiveNarrativeMemoryApiV1IntelligenceNarrativesActiveGetRequest', success_schema='GetActiveNarrativeMemoryApiV1IntelligenceNarrativesActiveGetSuccess', error_schema='GetActiveNarrativeMemoryApiV1IntelligenceNarrativesActiveGetError'),
    ContractRegistryEntry(registry_id='http:get_narrative_dominance_api_v1_intelligence_narratives_dominance_get', source_head=SOURCE_HEAD, operation=GETNARRATIVEDOMINANCEAPIV1INTELLIGENCENARRATIVESDOMINANCEGET_OPERATION, request_schema='GetNarrativeDominanceApiV1IntelligenceNarrativesDominanceGetRequest', success_schema='GetNarrativeDominanceApiV1IntelligenceNarrativesDominanceGetSuccess', error_schema='GetNarrativeDominanceApiV1IntelligenceNarrativesDominanceGetError'),
    ContractRegistryEntry(registry_id='http:get_dominant_narratives_api_v1_intelligence_narratives_dominant_get', source_head=SOURCE_HEAD, operation=GETDOMINANTNARRATIVESAPIV1INTELLIGENCENARRATIVESDOMINANTGET_OPERATION, request_schema='GetDominantNarrativesApiV1IntelligenceNarrativesDominantGetRequest', success_schema='GetDominantNarrativesApiV1IntelligenceNarrativesDominantGetSuccess', error_schema='GetDominantNarrativesApiV1IntelligenceNarrativesDominantGetError'),
    ContractRegistryEntry(registry_id='http:get_emerging_narratives_api_v1_intelligence_narratives_emerging_get', source_head=SOURCE_HEAD, operation=GETEMERGINGNARRATIVESAPIV1INTELLIGENCENARRATIVESEMERGINGGET_OPERATION, request_schema='GetEmergingNarrativesApiV1IntelligenceNarrativesEmergingGetRequest', success_schema='GetEmergingNarrativesApiV1IntelligenceNarrativesEmergingGetSuccess', error_schema='GetEmergingNarrativesApiV1IntelligenceNarrativesEmergingGetError'),
    ContractRegistryEntry(registry_id='http:get_falling_narratives_api_v1_intelligence_narratives_falling_get', source_head=SOURCE_HEAD, operation=GETFALLINGNARRATIVESAPIV1INTELLIGENCENARRATIVESFALLINGGET_OPERATION, request_schema='GetFallingNarrativesApiV1IntelligenceNarrativesFallingGetRequest', success_schema='GetFallingNarrativesApiV1IntelligenceNarrativesFallingGetSuccess', error_schema='GetFallingNarrativesApiV1IntelligenceNarrativesFallingGetError'),
    ContractRegistryEntry(registry_id='http:get_narrative_heatmap_api_v1_intelligence_narratives_heatmap_get', source_head=SOURCE_HEAD, operation=GETNARRATIVEHEATMAPAPIV1INTELLIGENCENARRATIVESHEATMAPGET_OPERATION, request_schema='GetNarrativeHeatmapApiV1IntelligenceNarrativesHeatmapGetRequest', success_schema='GetNarrativeHeatmapApiV1IntelligenceNarrativesHeatmapGetSuccess', error_schema='GetNarrativeHeatmapApiV1IntelligenceNarrativesHeatmapGetError'),
    ContractRegistryEntry(registry_id='http:get_narrative_history_api_v1_intelligence_narratives_history_get', source_head=SOURCE_HEAD, operation=GETNARRATIVEHISTORYAPIV1INTELLIGENCENARRATIVESHISTORYGET_OPERATION, request_schema='GetNarrativeHistoryApiV1IntelligenceNarrativesHistoryGetRequest', success_schema='GetNarrativeHistoryApiV1IntelligenceNarrativesHistoryGetSuccess', error_schema='GetNarrativeHistoryApiV1IntelligenceNarrativesHistoryGetError'),
    ContractRegistryEntry(registry_id='http:get_narrative_memory_api_v1_intelligence_narratives_memory_get', source_head=SOURCE_HEAD, operation=GETNARRATIVEMEMORYAPIV1INTELLIGENCENARRATIVESMEMORYGET_OPERATION, request_schema='GetNarrativeMemoryApiV1IntelligenceNarrativesMemoryGetRequest', success_schema='GetNarrativeMemoryApiV1IntelligenceNarrativesMemoryGetSuccess', error_schema='GetNarrativeMemoryApiV1IntelligenceNarrativesMemoryGetError'),
    ContractRegistryEntry(registry_id='http:get_rising_narratives_api_v1_intelligence_narratives_rising_get', source_head=SOURCE_HEAD, operation=GETRISINGNARRATIVESAPIV1INTELLIGENCENARRATIVESRISINGGET_OPERATION, request_schema='GetRisingNarrativesApiV1IntelligenceNarrativesRisingGetRequest', success_schema='GetRisingNarrativesApiV1IntelligenceNarrativesRisingGetSuccess', error_schema='GetRisingNarrativesApiV1IntelligenceNarrativesRisingGetError'),
    ContractRegistryEntry(registry_id='http:get_narrative_rotations_api_v1_intelligence_narratives_rotations_get', source_head=SOURCE_HEAD, operation=GETNARRATIVEROTATIONSAPIV1INTELLIGENCENARRATIVESROTATIONSGET_OPERATION, request_schema='GetNarrativeRotationsApiV1IntelligenceNarrativesRotationsGetRequest', success_schema='GetNarrativeRotationsApiV1IntelligenceNarrativesRotationsGetSuccess', error_schema='GetNarrativeRotationsApiV1IntelligenceNarrativesRotationsGetError'),
    ContractRegistryEntry(registry_id='http:get_top_narratives_api_v1_intelligence_narratives_top_get', source_head=SOURCE_HEAD, operation=GETTOPNARRATIVESAPIV1INTELLIGENCENARRATIVESTOPGET_OPERATION, request_schema='GetTopNarrativesApiV1IntelligenceNarrativesTopGetRequest', success_schema='GetTopNarrativesApiV1IntelligenceNarrativesTopGetSuccess', error_schema='GetTopNarrativesApiV1IntelligenceNarrativesTopGetError'),
    ContractRegistryEntry(registry_id='http:get_narrative_api_v1_intelligence_narratives__slug__get', source_head=SOURCE_HEAD, operation=GETNARRATIVEAPIV1INTELLIGENCENARRATIVESSLUGGET_OPERATION, request_schema='GetNarrativeApiV1IntelligenceNarrativesSlugGetRequest', success_schema='GetNarrativeApiV1IntelligenceNarrativesSlugGetSuccess', error_schema='GetNarrativeApiV1IntelligenceNarrativesSlugGetError'),
    ContractRegistryEntry(registry_id='http:list_market_patterns_api_v1_intelligence_patterns_get', source_head=SOURCE_HEAD, operation=LISTMARKETPATTERNSAPIV1INTELLIGENCEPATTERNSGET_OPERATION, request_schema='ListMarketPatternsApiV1IntelligencePatternsGetRequest', success_schema='ListMarketPatternsApiV1IntelligencePatternsGetSuccess', error_schema='ListMarketPatternsApiV1IntelligencePatternsGetError'),
    ContractRegistryEntry(registry_id='http:get_market_pattern_api_v1_intelligence_patterns__pattern_id__get', source_head=SOURCE_HEAD, operation=GETMARKETPATTERNAPIV1INTELLIGENCEPATTERNSPATTERNIDGET_OPERATION, request_schema='GetMarketPatternApiV1IntelligencePatternsPatternIdGetRequest', success_schema='GetMarketPatternApiV1IntelligencePatternsPatternIdGetSuccess', error_schema='GetMarketPatternApiV1IntelligencePatternsPatternIdGetError'),
    ContractRegistryEntry(registry_id='http:get_market_pattern_history_api_v1_intelligence_patterns__pattern_id__history_get', source_head=SOURCE_HEAD, operation=GETMARKETPATTERNHISTORYAPIV1INTELLIGENCEPATTERNSPATTERNIDHISTORYGET_OPERATION, request_schema='GetMarketPatternHistoryApiV1IntelligencePatternsPatternIdHistoryGetRequest', success_schema='GetMarketPatternHistoryApiV1IntelligencePatternsPatternIdHistoryGetSuccess', error_schema='GetMarketPatternHistoryApiV1IntelligencePatternsPatternIdHistoryGetError'),
    ContractRegistryEntry(registry_id='http:get_market_pattern_occurrences_api_v1_intelligence_patterns__pattern_id__occurrences_get', source_head=SOURCE_HEAD, operation=GETMARKETPATTERNOCCURRENCESAPIV1INTELLIGENCEPATTERNSPATTERNIDOCCURRENCESGET_OPERATION, request_schema='GetMarketPatternOccurrencesApiV1IntelligencePatternsPatternIdOccurrencesGetRequest', success_schema='GetMarketPatternOccurrencesApiV1IntelligencePatternsPatternIdOccurrencesGetSuccess', error_schema='GetMarketPatternOccurrencesApiV1IntelligencePatternsPatternIdOccurrencesGetError'),
    ContractRegistryEntry(registry_id='http:get_market_pattern_reaction_profile_api_v1_intelligence_patterns__pattern_id__reaction_profile_get', source_head=SOURCE_HEAD, operation=GETMARKETPATTERNREACTIONPROFILEAPIV1INTELLIGENCEPATTERNSPATTERNIDREACTIONPROFILEGET_OPERATION, request_schema='GetMarketPatternReactionProfileApiV1IntelligencePatternsPatternIdReactionProfileGetRequest', success_schema='GetMarketPatternReactionProfileApiV1IntelligencePatternsPatternIdReactionProfileGetSuccess', error_schema='GetMarketPatternReactionProfileApiV1IntelligencePatternsPatternIdReactionProfileGetError'),
    ContractRegistryEntry(registry_id='http:get_market_pattern_statistics_api_v1_intelligence_patterns__pattern_id__statistics_get', source_head=SOURCE_HEAD, operation=GETMARKETPATTERNSTATISTICSAPIV1INTELLIGENCEPATTERNSPATTERNIDSTATISTICSGET_OPERATION, request_schema='GetMarketPatternStatisticsApiV1IntelligencePatternsPatternIdStatisticsGetRequest', success_schema='GetMarketPatternStatisticsApiV1IntelligencePatternsPatternIdStatisticsGetSuccess', error_schema='GetMarketPatternStatisticsApiV1IntelligencePatternsPatternIdStatisticsGetError'),
    ContractRegistryEntry(registry_id='http:get_foundation_reaction_profile_api_v1_intelligence_reaction_profile__event_id__get', source_head=SOURCE_HEAD, operation=GETFOUNDATIONREACTIONPROFILEAPIV1INTELLIGENCEREACTIONPROFILEEVENTIDGET_OPERATION, request_schema='GetFoundationReactionProfileApiV1IntelligenceReactionProfileEventIdGetRequest', success_schema='GetFoundationReactionProfileApiV1IntelligenceReactionProfileEventIdGetSuccess', error_schema='GetFoundationReactionProfileApiV1IntelligenceReactionProfileEventIdGetError'),
    ContractRegistryEntry(registry_id='http:get_foundation_similar_events_api_v1_intelligence_similar_events__event_id__get', source_head=SOURCE_HEAD, operation=GETFOUNDATIONSIMILAREVENTSAPIV1INTELLIGENCESIMILAREVENTSEVENTIDGET_OPERATION, request_schema='GetFoundationSimilarEventsApiV1IntelligenceSimilarEventsEventIdGetRequest', success_schema='GetFoundationSimilarEventsApiV1IntelligenceSimilarEventsEventIdGetSuccess', error_schema='GetFoundationSimilarEventsApiV1IntelligenceSimilarEventsEventIdGetError'),
    ContractRegistryEntry(registry_id='http:get_article_similarity_report_api_v1_intelligence_similarity_articles__article_id__get', source_head=SOURCE_HEAD, operation=GETARTICLESIMILARITYREPORTAPIV1INTELLIGENCESIMILARITYARTICLESARTICLEIDGET_OPERATION, request_schema='GetArticleSimilarityReportApiV1IntelligenceSimilarityArticlesArticleIdGetRequest', success_schema='GetArticleSimilarityReportApiV1IntelligenceSimilarityArticlesArticleIdGetSuccess', error_schema='GetArticleSimilarityReportApiV1IntelligenceSimilarityArticlesArticleIdGetError'),
    ContractRegistryEntry(registry_id='http:get_candle_similarity_api_v1_intelligence_similarity_candle__candle_id__get', source_head=SOURCE_HEAD, operation=GETCANDLESIMILARITYAPIV1INTELLIGENCESIMILARITYCANDLECANDLEIDGET_OPERATION, request_schema='GetCandleSimilarityApiV1IntelligenceSimilarityCandleCandleIdGetRequest', success_schema='GetCandleSimilarityApiV1IntelligenceSimilarityCandleCandleIdGetSuccess', error_schema='GetCandleSimilarityApiV1IntelligenceSimilarityCandleCandleIdGetError'),
    ContractRegistryEntry(registry_id='http:get_event_similarity_api_v1_intelligence_similarity_event__event_id__get', source_head=SOURCE_HEAD, operation=GETEVENTSIMILARITYAPIV1INTELLIGENCESIMILARITYEVENTEVENTIDGET_OPERATION, request_schema='GetEventSimilarityApiV1IntelligenceSimilarityEventEventIdGetRequest', success_schema='GetEventSimilarityApiV1IntelligenceSimilarityEventEventIdGetSuccess', error_schema='GetEventSimilarityApiV1IntelligenceSimilarityEventEventIdGetError'),
    ContractRegistryEntry(registry_id='http:get_event_similarity_report_api_v1_intelligence_similarity_events__event_id__get', source_head=SOURCE_HEAD, operation=GETEVENTSIMILARITYREPORTAPIV1INTELLIGENCESIMILARITYEVENTSEVENTIDGET_OPERATION, request_schema='GetEventSimilarityReportApiV1IntelligenceSimilarityEventsEventIdGetRequest', success_schema='GetEventSimilarityReportApiV1IntelligenceSimilarityEventsEventIdGetSuccess', error_schema='GetEventSimilarityReportApiV1IntelligenceSimilarityEventsEventIdGetError'),
    ContractRegistryEntry(registry_id='http:get_news_similarity_api_v1_intelligence_similarity_news__event_id__get', source_head=SOURCE_HEAD, operation=GETNEWSSIMILARITYAPIV1INTELLIGENCESIMILARITYNEWSEVENTIDGET_OPERATION, request_schema='GetNewsSimilarityApiV1IntelligenceSimilarityNewsEventIdGetRequest', success_schema='GetNewsSimilarityApiV1IntelligenceSimilarityNewsEventIdGetSuccess', error_schema='GetNewsSimilarityApiV1IntelligenceSimilarityNewsEventIdGetError'),
    ContractRegistryEntry(registry_id='http:get_signal_similarity_report_api_v1_intelligence_similarity_signals__signal_id__get', source_head=SOURCE_HEAD, operation=GETSIGNALSIMILARITYREPORTAPIV1INTELLIGENCESIMILARITYSIGNALSSIGNALIDGET_OPERATION, request_schema='GetSignalSimilarityReportApiV1IntelligenceSimilaritySignalsSignalIdGetRequest', success_schema='GetSignalSimilarityReportApiV1IntelligenceSimilaritySignalsSignalIdGetSuccess', error_schema='GetSignalSimilarityReportApiV1IntelligenceSimilaritySignalsSignalIdGetError'),
    ContractRegistryEntry(registry_id='http:get_historical_similarity_context_api_v1_intelligence_similarity__event_id__get', source_head=SOURCE_HEAD, operation=GETHISTORICALSIMILARITYCONTEXTAPIV1INTELLIGENCESIMILARITYEVENTIDGET_OPERATION, request_schema='GetHistoricalSimilarityContextApiV1IntelligenceSimilarityEventIdGetRequest', success_schema='GetHistoricalSimilarityContextApiV1IntelligenceSimilarityEventIdGetSuccess', error_schema='GetHistoricalSimilarityContextApiV1IntelligenceSimilarityEventIdGetError'),
    ContractRegistryEntry(registry_id='http:get_historical_similarity_matches_api_v1_intelligence_similarity__event_id__matches_get', source_head=SOURCE_HEAD, operation=GETHISTORICALSIMILARITYMATCHESAPIV1INTELLIGENCESIMILARITYEVENTIDMATCHESGET_OPERATION, request_schema='GetHistoricalSimilarityMatchesApiV1IntelligenceSimilarityEventIdMatchesGetRequest', success_schema='GetHistoricalSimilarityMatchesApiV1IntelligenceSimilarityEventIdMatchesGetSuccess', error_schema='GetHistoricalSimilarityMatchesApiV1IntelligenceSimilarityEventIdMatchesGetError'),
    ContractRegistryEntry(registry_id='http:get_timeline_api_v1_intelligence_timeline_get', source_head=SOURCE_HEAD, operation=GETTIMELINEAPIV1INTELLIGENCETIMELINEGET_OPERATION, request_schema='GetTimelineApiV1IntelligenceTimelineGetRequest', success_schema='GetTimelineApiV1IntelligenceTimelineGetSuccess', error_schema='GetTimelineApiV1IntelligenceTimelineGetError'),
    ContractRegistryEntry(registry_id='http:get_context_api_v1_intelligence_timeline_context__timeline_event_id__get', source_head=SOURCE_HEAD, operation=GETCONTEXTAPIV1INTELLIGENCETIMELINECONTEXTTIMELINEEVENTIDGET_OPERATION, request_schema='GetContextApiV1IntelligenceTimelineContextTimelineEventIdGetRequest', success_schema='GetContextApiV1IntelligenceTimelineContextTimelineEventIdGetSuccess', error_schema='GetContextApiV1IntelligenceTimelineContextTimelineEventIdGetError'),
    ContractRegistryEntry(registry_id='http:get_timeline_day_api_v1_intelligence_timeline_day_get', source_head=SOURCE_HEAD, operation=GETTIMELINEDAYAPIV1INTELLIGENCETIMELINEDAYGET_OPERATION, request_schema='GetTimelineDayApiV1IntelligenceTimelineDayGetRequest', success_schema='GetTimelineDayApiV1IntelligenceTimelineDayGetSuccess', error_schema='GetTimelineDayApiV1IntelligenceTimelineDayGetError'),
    ContractRegistryEntry(registry_id='http:get_timeline_hour_api_v1_intelligence_timeline_hour_get', source_head=SOURCE_HEAD, operation=GETTIMELINEHOURAPIV1INTELLIGENCETIMELINEHOURGET_OPERATION, request_schema='GetTimelineHourApiV1IntelligenceTimelineHourGetRequest', success_schema='GetTimelineHourApiV1IntelligenceTimelineHourGetSuccess', error_schema='GetTimelineHourApiV1IntelligenceTimelineHourGetError'),
    ContractRegistryEntry(registry_id='http:get_latest_api_v1_intelligence_timeline_latest_get', source_head=SOURCE_HEAD, operation=GETLATESTAPIV1INTELLIGENCETIMELINELATESTGET_OPERATION, request_schema='GetLatestApiV1IntelligenceTimelineLatestGetRequest', success_schema='GetLatestApiV1IntelligenceTimelineLatestGetSuccess', error_schema='GetLatestApiV1IntelligenceTimelineLatestGetError'),
    ContractRegistryEntry(registry_id='http:current_narratives_api_v1_intelligence_timeline_narratives_current_get', source_head=SOURCE_HEAD, operation=CURRENTNARRATIVESAPIV1INTELLIGENCETIMELINENARRATIVESCURRENTGET_OPERATION, request_schema='CurrentNarrativesApiV1IntelligenceTimelineNarrativesCurrentGetRequest', success_schema='CurrentNarrativesApiV1IntelligenceTimelineNarrativesCurrentGetSuccess', error_schema='CurrentNarrativesApiV1IntelligenceTimelineNarrativesCurrentGetError'),
    ContractRegistryEntry(registry_id='http:high_confidence_news_impacts_api_v1_intelligence_timeline_news_impacts_high_confidence_get', source_head=SOURCE_HEAD, operation=HIGHCONFIDENCENEWSIMPACTSAPIV1INTELLIGENCETIMELINENEWSIMPACTSHIGHCONFIDENCEGET_OPERATION, request_schema='HighConfidenceNewsImpactsApiV1IntelligenceTimelineNewsImpactsHighConfidenceGetRequest', success_schema='HighConfidenceNewsImpactsApiV1IntelligenceTimelineNewsImpactsHighConfidenceGetSuccess', error_schema='HighConfidenceNewsImpactsApiV1IntelligenceTimelineNewsImpactsHighConfidenceGetError'),
    ContractRegistryEntry(registry_id='http:recent_news_impacts_api_v1_intelligence_timeline_news_impacts_recent_get', source_head=SOURCE_HEAD, operation=RECENTNEWSIMPACTSAPIV1INTELLIGENCETIMELINENEWSIMPACTSRECENTGET_OPERATION, request_schema='RecentNewsImpactsApiV1IntelligenceTimelineNewsImpactsRecentGetRequest', success_schema='RecentNewsImpactsApiV1IntelligenceTimelineNewsImpactsRecentGetSuccess', error_schema='RecentNewsImpactsApiV1IntelligenceTimelineNewsImpactsRecentGetError'),
    ContractRegistryEntry(registry_id='http:get_window_api_v1_intelligence_timeline_window_get', source_head=SOURCE_HEAD, operation=GETWINDOWAPIV1INTELLIGENCETIMELINEWINDOWGET_OPERATION, request_schema='GetWindowApiV1IntelligenceTimelineWindowGetRequest', success_schema='GetWindowApiV1IntelligenceTimelineWindowGetSuccess', error_schema='GetWindowApiV1IntelligenceTimelineWindowGetError'),
    ContractRegistryEntry(registry_id='http:candle_attribution_api_v1_market_time_machine_candle_attribution_get', source_head=SOURCE_HEAD, operation=CANDLEATTRIBUTIONAPIV1MARKETTIMEMACHINECANDLEATTRIBUTIONGET_OPERATION, request_schema='CandleAttributionApiV1MarketTimeMachineCandleAttributionGetRequest', success_schema='CandleAttributionApiV1MarketTimeMachineCandleAttributionGetSuccess', error_schema='CandleAttributionApiV1MarketTimeMachineCandleAttributionGetError'),
    ContractRegistryEntry(registry_id='http:market_events_api_v1_market_time_machine_events_get', source_head=SOURCE_HEAD, operation=MARKETEVENTSAPIV1MARKETTIMEMACHINEEVENTSGET_OPERATION, request_schema='MarketEventsApiV1MarketTimeMachineEventsGetRequest', success_schema='MarketEventsApiV1MarketTimeMachineEventsGetSuccess', error_schema='MarketEventsApiV1MarketTimeMachineEventsGetError'),
    ContractRegistryEntry(registry_id='http:news_impact_api_v1_market_time_machine_news_impact_get', source_head=SOURCE_HEAD, operation=NEWSIMPACTAPIV1MARKETTIMEMACHINENEWSIMPACTGET_OPERATION, request_schema='NewsImpactApiV1MarketTimeMachineNewsImpactGetRequest', success_schema='NewsImpactApiV1MarketTimeMachineNewsImpactGetSuccess', error_schema='NewsImpactApiV1MarketTimeMachineNewsImpactGetError'),
    ContractRegistryEntry(registry_id='http:provider_degradation_api_v1_market_time_machine_provider_degradation_get', source_head=SOURCE_HEAD, operation=PROVIDERDEGRADATIONAPIV1MARKETTIMEMACHINEPROVIDERDEGRADATIONGET_OPERATION, request_schema='ProviderDegradationApiV1MarketTimeMachineProviderDegradationGetRequest', success_schema='ProviderDegradationApiV1MarketTimeMachineProviderDegradationGetSuccess', error_schema='ProviderDegradationApiV1MarketTimeMachineProviderDegradationGetError'),
    ContractRegistryEntry(registry_id='http:reaction_windows_api_v1_market_time_machine_reaction_windows_get', source_head=SOURCE_HEAD, operation=REACTIONWINDOWSAPIV1MARKETTIMEMACHINEREACTIONWINDOWSGET_OPERATION, request_schema='ReactionWindowsApiV1MarketTimeMachineReactionWindowsGetRequest', success_schema='ReactionWindowsApiV1MarketTimeMachineReactionWindowsGetSuccess', error_schema='ReactionWindowsApiV1MarketTimeMachineReactionWindowsGetError'),
    ContractRegistryEntry(registry_id='http:regime_transitions_api_v1_market_time_machine_regime_transitions_get', source_head=SOURCE_HEAD, operation=REGIMETRANSITIONSAPIV1MARKETTIMEMACHINEREGIMETRANSITIONSGET_OPERATION, request_schema='RegimeTransitionsApiV1MarketTimeMachineRegimeTransitionsGetRequest', success_schema='RegimeTransitionsApiV1MarketTimeMachineRegimeTransitionsGetSuccess', error_schema='RegimeTransitionsApiV1MarketTimeMachineRegimeTransitionsGetError'),
    ContractRegistryEntry(registry_id='http:signal_reliability_api_v1_market_time_machine_signal_reliability_get', source_head=SOURCE_HEAD, operation=SIGNALRELIABILITYAPIV1MARKETTIMEMACHINESIGNALRELIABILITYGET_OPERATION, request_schema='SignalReliabilityApiV1MarketTimeMachineSignalReliabilityGetRequest', success_schema='SignalReliabilityApiV1MarketTimeMachineSignalReliabilityGetSuccess', error_schema='SignalReliabilityApiV1MarketTimeMachineSignalReliabilityGetError'),
    ContractRegistryEntry(registry_id='http:btc_candles_api_v1_market_btc_candles_get', source_head=SOURCE_HEAD, operation=BTCCANDLESAPIV1MARKETBTCCANDLESGET_OPERATION, request_schema='BtcCandlesApiV1MarketBtcCandlesGetRequest', success_schema='BtcCandlesApiV1MarketBtcCandlesGetSuccess', error_schema='BtcCandlesApiV1MarketBtcCandlesGetError'),
    ContractRegistryEntry(registry_id='http:btc_candles_latest_any_api_v1_market_btc_candles_latest_get', source_head=SOURCE_HEAD, operation=BTCCANDLESLATESTANYAPIV1MARKETBTCCANDLESLATESTGET_OPERATION, request_schema='BtcCandlesLatestAnyApiV1MarketBtcCandlesLatestGetRequest', success_schema='BtcCandlesLatestAnyApiV1MarketBtcCandlesLatestGetSuccess', error_schema='BtcCandlesLatestAnyApiV1MarketBtcCandlesLatestGetError'),
    ContractRegistryEntry(registry_id='http:btc_candle_by_id_api_v1_market_btc_candles__candle_id__get', source_head=SOURCE_HEAD, operation=BTCCANDLEBYIDAPIV1MARKETBTCCANDLESCANDLEIDGET_OPERATION, request_schema='BtcCandleByIdApiV1MarketBtcCandlesCandleIdGetRequest', success_schema='BtcCandleByIdApiV1MarketBtcCandlesCandleIdGetSuccess', error_schema='BtcCandleByIdApiV1MarketBtcCandlesCandleIdGetError'),
    ContractRegistryEntry(registry_id='http:btc_candle_evidence_api_v1_market_btc_candles__candle_id__evidence_get', source_head=SOURCE_HEAD, operation=BTCCANDLEEVIDENCEAPIV1MARKETBTCCANDLESCANDLEIDEVIDENCEGET_OPERATION, request_schema='BtcCandleEvidenceApiV1MarketBtcCandlesCandleIdEvidenceGetRequest', success_schema='BtcCandleEvidenceApiV1MarketBtcCandlesCandleIdEvidenceGetSuccess', error_schema='BtcCandleEvidenceApiV1MarketBtcCandlesCandleIdEvidenceGetError'),
    ContractRegistryEntry(registry_id='http:btc_candles_latest_api_v1_market_btc_candles__timeframe__latest_get', source_head=SOURCE_HEAD, operation=BTCCANDLESLATESTAPIV1MARKETBTCCANDLESTIMEFRAMELATESTGET_OPERATION, request_schema='BtcCandlesLatestApiV1MarketBtcCandlesTimeframeLatestGetRequest', success_schema='BtcCandlesLatestApiV1MarketBtcCandlesTimeframeLatestGetSuccess', error_schema='BtcCandlesLatestApiV1MarketBtcCandlesTimeframeLatestGetError'),
    ContractRegistryEntry(registry_id='http:btc_context_api_v1_market_btc_context_get', source_head=SOURCE_HEAD, operation=BTCCONTEXTAPIV1MARKETBTCCONTEXTGET_OPERATION, request_schema='BtcContextApiV1MarketBtcContextGetRequest', success_schema='BtcContextApiV1MarketBtcContextGetSuccess', error_schema='BtcContextApiV1MarketBtcContextGetError'),
    ContractRegistryEntry(registry_id='http:btc_price_api_v1_market_btc_price_get', source_head=SOURCE_HEAD, operation=BTCPRICEAPIV1MARKETBTCPRICEGET_OPERATION, request_schema='BtcPriceApiV1MarketBtcPriceGetRequest', success_schema='BtcPriceApiV1MarketBtcPriceGetSuccess', error_schema='BtcPriceApiV1MarketBtcPriceGetError'),
    ContractRegistryEntry(registry_id='http:btc_price_history_api_v1_market_btc_price_history_get', source_head=SOURCE_HEAD, operation=BTCPRICEHISTORYAPIV1MARKETBTCPRICEHISTORYGET_OPERATION, request_schema='BtcPriceHistoryApiV1MarketBtcPriceHistoryGetRequest', success_schema='BtcPriceHistoryApiV1MarketBtcPriceHistoryGetSuccess', error_schema='BtcPriceHistoryApiV1MarketBtcPriceHistoryGetError'),
    ContractRegistryEntry(registry_id='http:btc_providers_api_v1_market_btc_providers_get', source_head=SOURCE_HEAD, operation=BTCPROVIDERSAPIV1MARKETBTCPROVIDERSGET_OPERATION, request_schema='BtcProvidersApiV1MarketBtcProvidersGetRequest', success_schema='BtcProvidersApiV1MarketBtcProvidersGetSuccess', error_schema='BtcProvidersApiV1MarketBtcProvidersGetError'),
    ContractRegistryEntry(registry_id='http:btc_providers_health_api_v1_market_btc_providers_health_get', source_head=SOURCE_HEAD, operation=BTCPROVIDERSHEALTHAPIV1MARKETBTCPROVIDERSHEALTHGET_OPERATION, request_schema='BtcProvidersHealthApiV1MarketBtcProvidersHealthGetRequest', success_schema='BtcProvidersHealthApiV1MarketBtcProvidersHealthGetSuccess', error_schema='BtcProvidersHealthApiV1MarketBtcProvidersHealthGetError'),
    ContractRegistryEntry(registry_id='http:market_health_api_v1_market_health_get', source_head=SOURCE_HEAD, operation=MARKETHEALTHAPIV1MARKETHEALTHGET_OPERATION, request_schema='MarketHealthApiV1MarketHealthGetRequest', success_schema='MarketHealthApiV1MarketHealthGetSuccess', error_schema='MarketHealthApiV1MarketHealthGetError'),
    ContractRegistryEntry(registry_id='http:providers_health_api_v1_market_providers_health_get', source_head=SOURCE_HEAD, operation=PROVIDERSHEALTHAPIV1MARKETPROVIDERSHEALTHGET_OPERATION, request_schema='ProvidersHealthApiV1MarketProvidersHealthGetRequest', success_schema='ProvidersHealthApiV1MarketProvidersHealthGetSuccess', error_schema='ProvidersHealthApiV1MarketProvidersHealthGetError'),
    ContractRegistryEntry(registry_id='http:article_duplicates_api_v1_news_articles__article_id__duplicates_get', source_head=SOURCE_HEAD, operation=ARTICLEDUPLICATESAPIV1NEWSARTICLESARTICLEIDDUPLICATESGET_OPERATION, request_schema='ArticleDuplicatesApiV1NewsArticlesArticleIdDuplicatesGetRequest', success_schema='ArticleDuplicatesApiV1NewsArticlesArticleIdDuplicatesGetSuccess', error_schema='ArticleDuplicatesApiV1NewsArticlesArticleIdDuplicatesGetError'),
    ContractRegistryEntry(registry_id='http:by_sentiment_api_v1_news_by_sentiment__label__get', source_head=SOURCE_HEAD, operation=BYSENTIMENTAPIV1NEWSBYSENTIMENTLABELGET_OPERATION, request_schema='BySentimentApiV1NewsBySentimentLabelGetRequest', success_schema='BySentimentApiV1NewsBySentimentLabelGetSuccess', error_schema='BySentimentApiV1NewsBySentimentLabelGetError'),
    ContractRegistryEntry(registry_id='http:list_clusters_api_v1_news_clusters_get', source_head=SOURCE_HEAD, operation=LISTCLUSTERSAPIV1NEWSCLUSTERSGET_OPERATION, request_schema='ListClustersApiV1NewsClustersGetRequest', success_schema='ListClustersApiV1NewsClustersGetSuccess', error_schema='ListClustersApiV1NewsClustersGetError'),
    ContractRegistryEntry(registry_id='http:get_cluster_api_v1_news_clusters__cluster_id__get', source_head=SOURCE_HEAD, operation=GETCLUSTERAPIV1NEWSCLUSTERSCLUSTERIDGET_OPERATION, request_schema='GetClusterApiV1NewsClustersClusterIdGetRequest', success_schema='GetClusterApiV1NewsClustersClusterIdGetSuccess', error_schema='GetClusterApiV1NewsClustersClusterIdGetError'),
    ContractRegistryEntry(registry_id='http:list_events_api_v1_news_events_get', source_head=SOURCE_HEAD, operation=LISTEVENTSAPIV1NEWSEVENTSGET_OPERATION, request_schema='ListEventsApiV1NewsEventsGetRequest', success_schema='ListEventsApiV1NewsEventsGetSuccess', error_schema='ListEventsApiV1NewsEventsGetError'),
    ContractRegistryEntry(registry_id='http:high_impact_events_api_v1_news_events_high_impact_get', source_head=SOURCE_HEAD, operation=HIGHIMPACTEVENTSAPIV1NEWSEVENTSHIGHIMPACTGET_OPERATION, request_schema='HighImpactEventsApiV1NewsEventsHighImpactGetRequest', success_schema='HighImpactEventsApiV1NewsEventsHighImpactGetSuccess', error_schema='HighImpactEventsApiV1NewsEventsHighImpactGetError'),
    ContractRegistryEntry(registry_id='http:regulatory_events_api_v1_news_events_regulatory_get', source_head=SOURCE_HEAD, operation=REGULATORYEVENTSAPIV1NEWSEVENTSREGULATORYGET_OPERATION, request_schema='RegulatoryEventsApiV1NewsEventsRegulatoryGetRequest', success_schema='RegulatoryEventsApiV1NewsEventsRegulatoryGetSuccess', error_schema='RegulatoryEventsApiV1NewsEventsRegulatoryGetError'),
    ContractRegistryEntry(registry_id='http:security_events_api_v1_news_events_security_get', source_head=SOURCE_HEAD, operation=SECURITYEVENTSAPIV1NEWSEVENTSSECURITYGET_OPERATION, request_schema='SecurityEventsApiV1NewsEventsSecurityGetRequest', success_schema='SecurityEventsApiV1NewsEventsSecurityGetSuccess', error_schema='SecurityEventsApiV1NewsEventsSecurityGetError'),
    ContractRegistryEntry(registry_id='http:get_event_api_v1_news_events__event_id__get', source_head=SOURCE_HEAD, operation=GETEVENTAPIV1NEWSEVENTSEVENTIDGET_OPERATION, request_schema='GetEventApiV1NewsEventsEventIdGetRequest', success_schema='GetEventApiV1NewsEventsEventIdGetSuccess', error_schema='GetEventApiV1NewsEventsEventIdGetError'),
    ContractRegistryEntry(registry_id='http:get_event_articles_api_v1_news_events__event_id__articles_get', source_head=SOURCE_HEAD, operation=GETEVENTARTICLESAPIV1NEWSEVENTSEVENTIDARTICLESGET_OPERATION, request_schema='GetEventArticlesApiV1NewsEventsEventIdArticlesGetRequest', success_schema='GetEventArticlesApiV1NewsEventsEventIdArticlesGetSuccess', error_schema='GetEventArticlesApiV1NewsEventsEventIdArticlesGetError'),
    ContractRegistryEntry(registry_id='http:get_event_impact_api_v1_news_events__event_id__impact_get', source_head=SOURCE_HEAD, operation=GETEVENTIMPACTAPIV1NEWSEVENTSEVENTIDIMPACTGET_OPERATION, request_schema='GetEventImpactApiV1NewsEventsEventIdImpactGetRequest', success_schema='GetEventImpactApiV1NewsEventsEventIdImpactGetSuccess', error_schema='GetEventImpactApiV1NewsEventsEventIdImpactGetError'),
    ContractRegistryEntry(registry_id='http:get_event_score_api_v1_news_events__event_id__score_get', source_head=SOURCE_HEAD, operation=GETEVENTSCOREAPIV1NEWSEVENTSEVENTIDSCOREGET_OPERATION, request_schema='GetEventScoreApiV1NewsEventsEventIdScoreGetRequest', success_schema='GetEventScoreApiV1NewsEventsEventIdScoreGetSuccess', error_schema='GetEventScoreApiV1NewsEventsEventIdScoreGetError'),
    ContractRegistryEntry(registry_id='http:high_impact_news_api_v1_news_high_impact_get', source_head=SOURCE_HEAD, operation=HIGHIMPACTNEWSAPIV1NEWSHIGHIMPACTGET_OPERATION, request_schema='HighImpactNewsApiV1NewsHighImpactGetRequest', success_schema='HighImpactNewsApiV1NewsHighImpactGetSuccess', error_schema='HighImpactNewsApiV1NewsHighImpactGetError'),
    ContractRegistryEntry(registry_id='http:high_relevance_api_v1_news_high_relevance_get', source_head=SOURCE_HEAD, operation=HIGHRELEVANCEAPIV1NEWSHIGHRELEVANCEGET_OPERATION, request_schema='HighRelevanceApiV1NewsHighRelevanceGetRequest', success_schema='HighRelevanceApiV1NewsHighRelevanceGetSuccess', error_schema='HighRelevanceApiV1NewsHighRelevanceGetError'),
    ContractRegistryEntry(registry_id='http:latest_news_api_v1_news_latest_get', source_head=SOURCE_HEAD, operation=LATESTNEWSAPIV1NEWSLATESTGET_OPERATION, request_schema='LatestNewsApiV1NewsLatestGetRequest', success_schema='LatestNewsApiV1NewsLatestGetSuccess', error_schema='LatestNewsApiV1NewsLatestGetError'),
    ContractRegistryEntry(registry_id='http:regulatory_news_api_v1_news_regulatory_get', source_head=SOURCE_HEAD, operation=REGULATORYNEWSAPIV1NEWSREGULATORYGET_OPERATION, request_schema='RegulatoryNewsApiV1NewsRegulatoryGetRequest', success_schema='RegulatoryNewsApiV1NewsRegulatoryGetSuccess', error_schema='RegulatoryNewsApiV1NewsRegulatoryGetError'),
    ContractRegistryEntry(registry_id='http:security_news_api_v1_news_security_get', source_head=SOURCE_HEAD, operation=SECURITYNEWSAPIV1NEWSSECURITYGET_OPERATION, request_schema='SecurityNewsApiV1NewsSecurityGetRequest', success_schema='SecurityNewsApiV1NewsSecurityGetSuccess', error_schema='SecurityNewsApiV1NewsSecurityGetError'),
    ContractRegistryEntry(registry_id='http:list_sources_api_v1_news_sources_get', source_head=SOURCE_HEAD, operation=LISTSOURCESAPIV1NEWSSOURCESGET_OPERATION, request_schema='ListSourcesApiV1NewsSourcesGetRequest', success_schema='ListSourcesApiV1NewsSourcesGetSuccess', error_schema='ListSourcesApiV1NewsSourcesGetError'),
    ContractRegistryEntry(registry_id='http:categories_api_v1_news_sources_categories_get', source_head=SOURCE_HEAD, operation=CATEGORIESAPIV1NEWSSOURCESCATEGORIESGET_OPERATION, request_schema='CategoriesApiV1NewsSourcesCategoriesGetRequest', success_schema='CategoriesApiV1NewsSourcesCategoriesGetSuccess', error_schema='CategoriesApiV1NewsSourcesCategoriesGetError'),
    ContractRegistryEntry(registry_id='http:sources_health_api_v1_news_sources_health_get', source_head=SOURCE_HEAD, operation=SOURCESHEALTHAPIV1NEWSSOURCESHEALTHGET_OPERATION, request_schema='SourcesHealthApiV1NewsSourcesHealthGetRequest', success_schema='SourcesHealthApiV1NewsSourcesHealthGetSuccess', error_schema='SourcesHealthApiV1NewsSourcesHealthGetError'),
    ContractRegistryEntry(registry_id='http:list_source_reputation_api_v1_news_sources_reputation_get', source_head=SOURCE_HEAD, operation=LISTSOURCEREPUTATIONAPIV1NEWSSOURCESREPUTATIONGET_OPERATION, request_schema='ListSourceReputationApiV1NewsSourcesReputationGetRequest', success_schema='ListSourceReputationApiV1NewsSourcesReputationGetSuccess', error_schema='ListSourceReputationApiV1NewsSourcesReputationGetError'),
    ContractRegistryEntry(registry_id='http:tiers_api_v1_news_sources_tiers_get', source_head=SOURCE_HEAD, operation=TIERSAPIV1NEWSSOURCESTIERSGET_OPERATION, request_schema='TiersApiV1NewsSourcesTiersGetRequest', success_schema='TiersApiV1NewsSourcesTiersGetSuccess', error_schema='TiersApiV1NewsSourcesTiersGetError'),
    ContractRegistryEntry(registry_id='http:get_source_api_v1_news_sources__source_id__get', source_head=SOURCE_HEAD, operation=GETSOURCEAPIV1NEWSSOURCESSOURCEIDGET_OPERATION, request_schema='GetSourceApiV1NewsSourcesSourceIdGetRequest', success_schema='GetSourceApiV1NewsSourcesSourceIdGetSuccess', error_schema='GetSourceApiV1NewsSourcesSourceIdGetError'),
    ContractRegistryEntry(registry_id='http:source_confidence_events_api_v1_news_sources__source_id__confidence_events_get', source_head=SOURCE_HEAD, operation=SOURCECONFIDENCEEVENTSAPIV1NEWSSOURCESSOURCEIDCONFIDENCEEVENTSGET_OPERATION, request_schema='SourceConfidenceEventsApiV1NewsSourcesSourceIdConfidenceEventsGetRequest', success_schema='SourceConfidenceEventsApiV1NewsSourcesSourceIdConfidenceEventsGetSuccess', error_schema='SourceConfidenceEventsApiV1NewsSourcesSourceIdConfidenceEventsGetError'),
    ContractRegistryEntry(registry_id='http:source_health_api_v1_news_sources__source_id__health_get', source_head=SOURCE_HEAD, operation=SOURCEHEALTHAPIV1NEWSSOURCESSOURCEIDHEALTHGET_OPERATION, request_schema='SourceHealthApiV1NewsSourcesSourceIdHealthGetRequest', success_schema='SourceHealthApiV1NewsSourcesSourceIdHealthGetSuccess', error_schema='SourceHealthApiV1NewsSourcesSourceIdHealthGetError'),
    ContractRegistryEntry(registry_id='http:source_snapshots_api_v1_news_sources__source_id__snapshots_get', source_head=SOURCE_HEAD, operation=SOURCESNAPSHOTSAPIV1NEWSSOURCESSOURCEIDSNAPSHOTSGET_OPERATION, request_schema='SourceSnapshotsApiV1NewsSourcesSourceIdSnapshotsGetRequest', success_schema='SourceSnapshotsApiV1NewsSourcesSourceIdSnapshotsGetSuccess', error_schema='SourceSnapshotsApiV1NewsSourcesSourceIdSnapshotsGetError'),
    ContractRegistryEntry(registry_id='http:get_article_explanation_api_v1_news__article_id__explanation_get', source_head=SOURCE_HEAD, operation=GETARTICLEEXPLANATIONAPIV1NEWSARTICLEIDEXPLANATIONGET_OPERATION, request_schema='GetArticleExplanationApiV1NewsArticleIdExplanationGetRequest', success_schema='GetArticleExplanationApiV1NewsArticleIdExplanationGetSuccess', error_schema='GetArticleExplanationApiV1NewsArticleIdExplanationGetError'),
    ContractRegistryEntry(registry_id='http:get_article_impact_api_v1_news__article_id__impact_get', source_head=SOURCE_HEAD, operation=GETARTICLEIMPACTAPIV1NEWSARTICLEIDIMPACTGET_OPERATION, request_schema='GetArticleImpactApiV1NewsArticleIdImpactGetRequest', success_schema='GetArticleImpactApiV1NewsArticleIdImpactGetSuccess', error_schema='GetArticleImpactApiV1NewsArticleIdImpactGetError'),
    ContractRegistryEntry(registry_id='http:get_article_narratives_api_v1_news__article_id__narratives_get', source_head=SOURCE_HEAD, operation=GETARTICLENARRATIVESAPIV1NEWSARTICLEIDNARRATIVESGET_OPERATION, request_schema='GetArticleNarrativesApiV1NewsArticleIdNarrativesGetRequest', success_schema='GetArticleNarrativesApiV1NewsArticleIdNarrativesGetSuccess', error_schema='GetArticleNarrativesApiV1NewsArticleIdNarrativesGetError'),
    ContractRegistryEntry(registry_id='http:get_article_score_api_v1_news__article_id__score_get', source_head=SOURCE_HEAD, operation=GETARTICLESCOREAPIV1NEWSARTICLEIDSCOREGET_OPERATION, request_schema='GetArticleScoreApiV1NewsArticleIdScoreGetRequest', success_schema='GetArticleScoreApiV1NewsArticleIdScoreGetSuccess', error_schema='GetArticleScoreApiV1NewsArticleIdScoreGetError'),
    ContractRegistryEntry(registry_id='http:get_article_scores_api_v1_news__article_id__scores_get', source_head=SOURCE_HEAD, operation=GETARTICLESCORESAPIV1NEWSARTICLEIDSCORESGET_OPERATION, request_schema='GetArticleScoresApiV1NewsArticleIdScoresGetRequest', success_schema='GetArticleScoresApiV1NewsArticleIdScoresGetSuccess', error_schema='GetArticleScoresApiV1NewsArticleIdScoresGetError'),
    ContractRegistryEntry(registry_id='http:onchain_events_api_v1_onchain_events_get', source_head=SOURCE_HEAD, operation=ONCHAINEVENTSAPIV1ONCHAINEVENTSGET_OPERATION, request_schema='OnchainEventsApiV1OnchainEventsGetRequest', success_schema='OnchainEventsApiV1OnchainEventsGetSuccess', error_schema='OnchainEventsApiV1OnchainEventsGetError'),
    ContractRegistryEntry(registry_id='http:onchain_state_api_v1_onchain_state_get', source_head=SOURCE_HEAD, operation=ONCHAINSTATEAPIV1ONCHAINSTATEGET_OPERATION, request_schema='OnchainStateApiV1OnchainStateGetRequest', success_schema='OnchainStateApiV1OnchainStateGetSuccess', error_schema='OnchainStateApiV1OnchainStateGetError'),
    ContractRegistryEntry(registry_id='http:public_features_api_v1_public_features_get', source_head=SOURCE_HEAD, operation=PUBLICFEATURESAPIV1PUBLICFEATURESGET_OPERATION, request_schema='PublicFeaturesApiV1PublicFeaturesGetRequest', success_schema='PublicFeaturesApiV1PublicFeaturesGetSuccess', error_schema='PublicFeaturesApiV1PublicFeaturesGetError'),
    ContractRegistryEntry(registry_id='http:public_landing_api_v1_public_landing_get', source_head=SOURCE_HEAD, operation=PUBLICLANDINGAPIV1PUBLICLANDINGGET_OPERATION, request_schema='PublicLandingApiV1PublicLandingGetRequest', success_schema='PublicLandingApiV1PublicLandingGetSuccess', error_schema='PublicLandingApiV1PublicLandingGetError'),
    ContractRegistryEntry(registry_id='http:public_roadmap_api_v1_public_roadmap_get', source_head=SOURCE_HEAD, operation=PUBLICROADMAPAPIV1PUBLICROADMAPGET_OPERATION, request_schema='PublicRoadmapApiV1PublicRoadmapGetRequest', success_schema='PublicRoadmapApiV1PublicRoadmapGetSuccess', error_schema='PublicRoadmapApiV1PublicRoadmapGetError'),
    ContractRegistryEntry(registry_id='http:public_stats_api_v1_public_stats_get', source_head=SOURCE_HEAD, operation=PUBLICSTATSAPIV1PUBLICSTATSGET_OPERATION, request_schema='PublicStatsApiV1PublicStatsGetRequest', success_schema='PublicStatsApiV1PublicStatsGetSuccess', error_schema='PublicStatsApiV1PublicStatsGetError'),
    ContractRegistryEntry(registry_id='http:public_status_api_v1_public_status_get', source_head=SOURCE_HEAD, operation=PUBLICSTATUSAPIV1PUBLICSTATUSGET_OPERATION, request_schema='PublicStatusApiV1PublicStatusGetRequest', success_schema='PublicStatusApiV1PublicStatusGetSuccess', error_schema='PublicStatusApiV1PublicStatusGetError'),
    ContractRegistryEntry(registry_id='http:public_trace_summary_api_v1_public_trace__report_id__summary_get', source_head=SOURCE_HEAD, operation=PUBLICTRACESUMMARYAPIV1PUBLICTRACEREPORTIDSUMMARYGET_OPERATION, request_schema='PublicTraceSummaryApiV1PublicTraceReportIdSummaryGetRequest', success_schema='PublicTraceSummaryApiV1PublicTraceReportIdSummaryGetSuccess', error_schema='PublicTraceSummaryApiV1PublicTraceReportIdSummaryGetError'),
    ContractRegistryEntry(registry_id='http:latest_signals_api_v1_signals_latest_get', source_head=SOURCE_HEAD, operation=LATESTSIGNALSAPIV1SIGNALSLATESTGET_OPERATION, request_schema='LatestSignalsApiV1SignalsLatestGetRequest', success_schema='LatestSignalsApiV1SignalsLatestGetSuccess', error_schema='LatestSignalsApiV1SignalsLatestGetError'),
    ContractRegistryEntry(registry_id='http:news_market_impact_signals_api_v1_signals_news_market_impact_get', source_head=SOURCE_HEAD, operation=NEWSMARKETIMPACTSIGNALSAPIV1SIGNALSNEWSMARKETIMPACTGET_OPERATION, request_schema='NewsMarketImpactSignalsApiV1SignalsNewsMarketImpactGetRequest', success_schema='NewsMarketImpactSignalsApiV1SignalsNewsMarketImpactGetSuccess', error_schema='NewsMarketImpactSignalsApiV1SignalsNewsMarketImpactGetError'),
    ContractRegistryEntry(registry_id='http:top_signals_api_v1_signals_top_get', source_head=SOURCE_HEAD, operation=TOPSIGNALSAPIV1SIGNALSTOPGET_OPERATION, request_schema='TopSignalsApiV1SignalsTopGetRequest', success_schema='TopSignalsApiV1SignalsTopGetSuccess', error_schema='TopSignalsApiV1SignalsTopGetError'),
    ContractRegistryEntry(registry_id='http:get_signal_api_v1_signals__signal_id__get', source_head=SOURCE_HEAD, operation=GETSIGNALAPIV1SIGNALSSIGNALIDGET_OPERATION, request_schema='GetSignalApiV1SignalsSignalIdGetRequest', success_schema='GetSignalApiV1SignalsSignalIdGetSuccess', error_schema='GetSignalApiV1SignalsSignalIdGetError'),
    ContractRegistryEntry(registry_id='http:get_signal_delivery_logs_api_v1_signals__signal_id__delivery_logs_get', source_head=SOURCE_HEAD, operation=GETSIGNALDELIVERYLOGSAPIV1SIGNALSSIGNALIDDELIVERYLOGSGET_OPERATION, request_schema='GetSignalDeliveryLogsApiV1SignalsSignalIdDeliveryLogsGetRequest', success_schema='GetSignalDeliveryLogsApiV1SignalsSignalIdDeliveryLogsGetSuccess', error_schema='GetSignalDeliveryLogsApiV1SignalsSignalIdDeliveryLogsGetError'),
    ContractRegistryEntry(registry_id='http:get_signal_evidence_api_v1_signals__signal_id__evidence_get', source_head=SOURCE_HEAD, operation=GETSIGNALEVIDENCEAPIV1SIGNALSSIGNALIDEVIDENCEGET_OPERATION, request_schema='GetSignalEvidenceApiV1SignalsSignalIdEvidenceGetRequest', success_schema='GetSignalEvidenceApiV1SignalsSignalIdEvidenceGetSuccess', error_schema='GetSignalEvidenceApiV1SignalsSignalIdEvidenceGetError'),
    ContractRegistryEntry(registry_id='http:signal_explanation_api_v1_signals__signal_id__explanation_get', source_head=SOURCE_HEAD, operation=SIGNALEXPLANATIONAPIV1SIGNALSSIGNALIDEXPLANATIONGET_OPERATION, request_schema='SignalExplanationApiV1SignalsSignalIdExplanationGetRequest', success_schema='SignalExplanationApiV1SignalsSignalIdExplanationGetSuccess', error_schema='SignalExplanationApiV1SignalsSignalIdExplanationGetError'),
    ContractRegistryEntry(registry_id='http:signal_recommendations_api_v1_signals__signal_id__recommendations_get', source_head=SOURCE_HEAD, operation=SIGNALRECOMMENDATIONSAPIV1SIGNALSSIGNALIDRECOMMENDATIONSGET_OPERATION, request_schema='SignalRecommendationsApiV1SignalsSignalIdRecommendationsGetRequest', success_schema='SignalRecommendationsApiV1SignalsSignalIdRecommendationsGetSuccess', error_schema='SignalRecommendationsApiV1SignalsSignalIdRecommendationsGetError'),
    ContractRegistryEntry(registry_id='http:storage_status_api_v1_storage_status_get', source_head=SOURCE_HEAD, operation=STORAGESTATUSAPIV1STORAGESTATUSGET_OPERATION, request_schema='StorageStatusApiV1StorageStatusGetRequest', success_schema='StorageStatusApiV1StorageStatusGetSuccess', error_schema='StorageStatusApiV1StorageStatusGetError'),
    ContractRegistryEntry(registry_id='http:timescale_operations_status_api_v1_storage_timescale_status_get', source_head=SOURCE_HEAD, operation=TIMESCALEOPERATIONSSTATUSAPIV1STORAGETIMESCALESTATUSGET_OPERATION, request_schema='TimescaleOperationsStatusApiV1StorageTimescaleStatusGetRequest', success_schema='TimescaleOperationsStatusApiV1StorageTimescaleStatusGetSuccess', error_schema='TimescaleOperationsStatusApiV1StorageTimescaleStatusGetError'),
    ContractRegistryEntry(registry_id='http:analyze_address_api_v1_trace_address__address__get', source_head=SOURCE_HEAD, operation=ANALYZEADDRESSAPIV1TRACEADDRESSADDRESSGET_OPERATION, request_schema='AnalyzeAddressApiV1TraceAddressAddressGetRequest', success_schema='AnalyzeAddressApiV1TraceAddressAddressGetSuccess', error_schema='AnalyzeAddressApiV1TraceAddressAddressGetError'),
    ContractRegistryEntry(registry_id='http:trace_alerts_api_v1_trace_alerts_get', source_head=SOURCE_HEAD, operation=TRACEALERTSAPIV1TRACEALERTSGET_OPERATION, request_schema='TraceAlertsApiV1TraceAlertsGetRequest', success_schema='TraceAlertsApiV1TraceAlertsGetSuccess', error_schema='TraceAlertsApiV1TraceAlertsGetError'),
    ContractRegistryEntry(registry_id='http:trace_events_api_v1_trace_events_get', source_head=SOURCE_HEAD, operation=TRACEEVENTSAPIV1TRACEEVENTSGET_OPERATION, request_schema='TraceEventsApiV1TraceEventsGetRequest', success_schema='TraceEventsApiV1TraceEventsGetSuccess', error_schema='TraceEventsApiV1TraceEventsGetError'),
    ContractRegistryEntry(registry_id='http:trace_event_api_v1_trace_events__event_id__get', source_head=SOURCE_HEAD, operation=TRACEEVENTAPIV1TRACEEVENTSEVENTIDGET_OPERATION, request_schema='TraceEventApiV1TraceEventsEventIdGetRequest', success_schema='TraceEventApiV1TraceEventsEventIdGetSuccess', error_schema='TraceEventApiV1TraceEventsEventIdGetError'),
    ContractRegistryEntry(registry_id='http:lite_address_check_api_v1_trace_lite__address__get', source_head=SOURCE_HEAD, operation=LITEADDRESSCHECKAPIV1TRACELITEADDRESSGET_OPERATION, request_schema='LiteAddressCheckApiV1TraceLiteAddressGetRequest', success_schema='LiteAddressCheckApiV1TraceLiteAddressGetSuccess', error_schema='LiteAddressCheckApiV1TraceLiteAddressGetError'),
    ContractRegistryEntry(registry_id='http:get_report_api_v1_trace_report__report_id__get', source_head=SOURCE_HEAD, operation=GETREPORTAPIV1TRACEREPORTREPORTIDGET_OPERATION, request_schema='GetReportApiV1TraceReportReportIdGetRequest', success_schema='GetReportApiV1TraceReportReportIdGetSuccess', error_schema='GetReportApiV1TraceReportReportIdGetError'),
    ContractRegistryEntry(registry_id='http:trace_citadel_contribution_api_v1_trace_report__report_id__citadel_contribution_get', source_head=SOURCE_HEAD, operation=TRACECITADELCONTRIBUTIONAPIV1TRACEREPORTREPORTIDCITADELCONTRIBUTIONGET_OPERATION, request_schema='TraceCitadelContributionApiV1TraceReportReportIdCitadelContributionGetRequest', success_schema='TraceCitadelContributionApiV1TraceReportReportIdCitadelContributionGetSuccess', error_schema='TraceCitadelContributionApiV1TraceReportReportIdCitadelContributionGetError'),
    ContractRegistryEntry(registry_id='http:get_counterparty_lens_api_v1_trace_report__report_id__counterparty_lens_get', source_head=SOURCE_HEAD, operation=GETCOUNTERPARTYLENSAPIV1TRACEREPORTREPORTIDCOUNTERPARTYLENSGET_OPERATION, request_schema='GetCounterpartyLensApiV1TraceReportReportIdCounterpartyLensGetRequest', success_schema='GetCounterpartyLensApiV1TraceReportReportIdCounterpartyLensGetSuccess', error_schema='GetCounterpartyLensApiV1TraceReportReportIdCounterpartyLensGetError'),
    ContractRegistryEntry(registry_id='http:get_dust_radar_api_v1_trace_report__report_id__dust_radar_get', source_head=SOURCE_HEAD, operation=GETDUSTRADARAPIV1TRACEREPORTREPORTIDDUSTRADARGET_OPERATION, request_schema='GetDustRadarApiV1TraceReportReportIdDustRadarGetRequest', success_schema='GetDustRadarApiV1TraceReportReportIdDustRadarGetSuccess', error_schema='GetDustRadarApiV1TraceReportReportIdDustRadarGetError'),
    ContractRegistryEntry(registry_id='http:list_evidence_api_v1_trace_report__report_id__evidence_get', source_head=SOURCE_HEAD, operation=LISTEVIDENCEAPIV1TRACEREPORTREPORTIDEVIDENCEGET_OPERATION, request_schema='ListEvidenceApiV1TraceReportReportIdEvidenceGetRequest', success_schema='ListEvidenceApiV1TraceReportReportIdEvidenceGetSuccess', error_schema='ListEvidenceApiV1TraceReportReportIdEvidenceGetError'),
    ContractRegistryEntry(registry_id='http:trace_evidence_refs_api_v1_trace_report__report_id__evidence_refs_get', source_head=SOURCE_HEAD, operation=TRACEEVIDENCEREFSAPIV1TRACEREPORTREPORTIDEVIDENCEREFSGET_OPERATION, request_schema='TraceEvidenceRefsApiV1TraceReportReportIdEvidenceRefsGetRequest', success_schema='TraceEvidenceRefsApiV1TraceReportReportIdEvidenceRefsGetSuccess', error_schema='TraceEvidenceRefsApiV1TraceReportReportIdEvidenceRefsGetError'),
    ContractRegistryEntry(registry_id='http:get_origin_passport_api_v1_trace_report__report_id__origin_passport_get', source_head=SOURCE_HEAD, operation=GETORIGINPASSPORTAPIV1TRACEREPORTREPORTIDORIGINPASSPORTGET_OPERATION, request_schema='GetOriginPassportApiV1TraceReportReportIdOriginPassportGetRequest', success_schema='GetOriginPassportApiV1TraceReportReportIdOriginPassportGetSuccess', error_schema='GetOriginPassportApiV1TraceReportReportIdOriginPassportGetError'),
    ContractRegistryEntry(registry_id='http:trace_policy_facts_api_v1_trace_report__report_id__policy_facts_get', source_head=SOURCE_HEAD, operation=TRACEPOLICYFACTSAPIV1TRACEREPORTREPORTIDPOLICYFACTSGET_OPERATION, request_schema='TracePolicyFactsApiV1TraceReportReportIdPolicyFactsGetRequest', success_schema='TracePolicyFactsApiV1TraceReportReportIdPolicyFactsGetSuccess', error_schema='TracePolicyFactsApiV1TraceReportReportIdPolicyFactsGetError'),
    ContractRegistryEntry(registry_id='http:get_privacy_shield_api_v1_trace_report__report_id__privacy_shield_get', source_head=SOURCE_HEAD, operation=GETPRIVACYSHIELDAPIV1TRACEREPORTREPORTIDPRIVACYSHIELDGET_OPERATION, request_schema='GetPrivacyShieldApiV1TraceReportReportIdPrivacyShieldGetRequest', success_schema='GetPrivacyShieldApiV1TraceReportReportIdPrivacyShieldGetSuccess', error_schema='GetPrivacyShieldApiV1TraceReportReportIdPrivacyShieldGetError'),
    ContractRegistryEntry(registry_id='http:get_proof_packet_api_v1_trace_report__report_id__proof_packet_get', source_head=SOURCE_HEAD, operation=GETPROOFPACKETAPIV1TRACEREPORTREPORTIDPROOFPACKETGET_OPERATION, request_schema='GetProofPacketApiV1TraceReportReportIdProofPacketGetRequest', success_schema='GetProofPacketApiV1TraceReportReportIdProofPacketGetSuccess', error_schema='GetProofPacketApiV1TraceReportReportIdProofPacketGetError'),
    ContractRegistryEntry(registry_id='http:get_provider_disagreement_api_v1_trace_report__report_id__provider_disagreement_get', source_head=SOURCE_HEAD, operation=GETPROVIDERDISAGREEMENTAPIV1TRACEREPORTREPORTIDPROVIDERDISAGREEMENTGET_OPERATION, request_schema='GetProviderDisagreementApiV1TraceReportReportIdProviderDisagreementGetRequest', success_schema='GetProviderDisagreementApiV1TraceReportReportIdProviderDisagreementGetSuccess', error_schema='GetProviderDisagreementApiV1TraceReportReportIdProviderDisagreementGetError'),
    ContractRegistryEntry(registry_id='http:get_source_summary_api_v1_trace_report__report_id__source_summary_get', source_head=SOURCE_HEAD, operation=GETSOURCESUMMARYAPIV1TRACEREPORTREPORTIDSOURCESUMMARYGET_OPERATION, request_schema='GetSourceSummaryApiV1TraceReportReportIdSourceSummaryGetRequest', success_schema='GetSourceSummaryApiV1TraceReportReportIdSourceSummaryGetSuccess', error_schema='GetSourceSummaryApiV1TraceReportReportIdSourceSummaryGetError'),
    ContractRegistryEntry(registry_id='http:get_utxo_hygiene_api_v1_trace_report__report_id__utxo_hygiene_get', source_head=SOURCE_HEAD, operation=GETUTXOHYGIENEAPIV1TRACEREPORTREPORTIDUTXOHYGIENEGET_OPERATION, request_schema='GetUtxoHygieneApiV1TraceReportReportIdUtxoHygieneGetRequest', success_schema='GetUtxoHygieneApiV1TraceReportReportIdUtxoHygieneGetSuccess', error_schema='GetUtxoHygieneApiV1TraceReportReportIdUtxoHygieneGetError'),
    ContractRegistryEntry(registry_id='http:list_sources_api_v1_trace_sources_get', source_head=SOURCE_HEAD, operation=LISTSOURCESAPIV1TRACESOURCESGET_OPERATION, request_schema='ListSourcesApiV1TraceSourcesGetRequest', success_schema='ListSourcesApiV1TraceSourcesGetSuccess', error_schema='ListSourcesApiV1TraceSourcesGetError'),
    ContractRegistryEntry(registry_id='http:get_source_api_v1_trace_sources__source_name__get', source_head=SOURCE_HEAD, operation=GETSOURCEAPIV1TRACESOURCESSOURCENAMEGET_OPERATION, request_schema='GetSourceApiV1TraceSourcesSourceNameGetRequest', success_schema='GetSourceApiV1TraceSourcesSourceNameGetSuccess', error_schema='GetSourceApiV1TraceSourcesSourceNameGetError'),
    ContractRegistryEntry(registry_id='http:trace_status_api_v1_trace_status_get', source_head=SOURCE_HEAD, operation=TRACESTATUSAPIV1TRACESTATUSGET_OPERATION, request_schema='TraceStatusApiV1TraceStatusGetRequest', success_schema='TraceStatusApiV1TraceStatusGetSuccess', error_schema='TraceStatusApiV1TraceStatusGetError'),
    ContractRegistryEntry(registry_id='http:list_watchlist_api_v1_trace_watchlist_get', source_head=SOURCE_HEAD, operation=LISTWATCHLISTAPIV1TRACEWATCHLISTGET_OPERATION, request_schema='ListWatchlistApiV1TraceWatchlistGetRequest', success_schema='ListWatchlistApiV1TraceWatchlistGetSuccess', error_schema='ListWatchlistApiV1TraceWatchlistGetError'),
    ContractRegistryEntry(registry_id='http:dependencies_health_dependencies_get', source_head=SOURCE_HEAD, operation=DEPENDENCIESHEALTHDEPENDENCIESGET_OPERATION, request_schema='DependenciesHealthDependenciesGetRequest', success_schema='DependenciesHealthDependenciesGetSuccess', error_schema='DependenciesHealthDependenciesGetError'),
    ContractRegistryEntry(registry_id='http:intelligence_health_intelligence_get', source_head=SOURCE_HEAD, operation=INTELLIGENCEHEALTHINTELLIGENCEGET_OPERATION, request_schema='IntelligenceHealthIntelligenceGetRequest', success_schema='IntelligenceHealthIntelligenceGetSuccess', error_schema='IntelligenceHealthIntelligenceGetError'),
    ContractRegistryEntry(registry_id='http:live_health_live_get', source_head=SOURCE_HEAD, operation=LIVEHEALTHLIVEGET_OPERATION, request_schema='LiveHealthLiveGetRequest', success_schema='LiveHealthLiveGetSuccess', error_schema='LiveHealthLiveGetError'),
    ContractRegistryEntry(registry_id='http:operations_health_operations_get', source_head=SOURCE_HEAD, operation=OPERATIONSHEALTHOPERATIONSGET_OPERATION, request_schema='OperationsHealthOperationsGetRequest', success_schema='OperationsHealthOperationsGetSuccess', error_schema='OperationsHealthOperationsGetError'),
    ContractRegistryEntry(registry_id='http:providers_health_providers_get', source_head=SOURCE_HEAD, operation=PROVIDERSHEALTHPROVIDERSGET_OPERATION, request_schema='ProvidersHealthProvidersGetRequest', success_schema='ProvidersHealthProvidersGetSuccess', error_schema='ProvidersHealthProvidersGetError'),
    ContractRegistryEntry(registry_id='http:ready_health_ready_get', source_head=SOURCE_HEAD, operation=READYHEALTHREADYGET_OPERATION, request_schema='ReadyHealthReadyGetRequest', success_schema='ReadyHealthReadyGetSuccess', error_schema='ReadyHealthReadyGetError'),
    ContractRegistryEntry(registry_id='http:startup_health_startup_get', source_head=SOURCE_HEAD, operation=STARTUPHEALTHSTARTUPGET_OPERATION, request_schema='StartupHealthStartupGetRequest', success_schema='StartupHealthStartupGetSuccess', error_schema='StartupHealthStartupGetError'),
    ContractRegistryEntry(registry_id='http:web_candle_dto_web_candle__candle_id__get', source_head=SOURCE_HEAD, operation=WEBCANDLEDTOWEBCANDLECANDLEIDGET_OPERATION, request_schema='WebCandleDtoWebCandleCandleIdGetRequest', success_schema='WebCandleDtoWebCandleCandleIdGetSuccess', error_schema='WebCandleDtoWebCandleCandleIdGetError'),
    ContractRegistryEntry(registry_id='http:web_evidence_dto_web_evidence__packet_id__get', source_head=SOURCE_HEAD, operation=WEBEVIDENCEDTOWEBEVIDENCEPACKETIDGET_OPERATION, request_schema='WebEvidenceDtoWebEvidencePacketIdGetRequest', success_schema='WebEvidenceDtoWebEvidencePacketIdGetSuccess', error_schema='WebEvidenceDtoWebEvidencePacketIdGetError'),
    ContractRegistryEntry(registry_id='http:web_market_time_machine_dto_web_market_time_machine_get', source_head=SOURCE_HEAD, operation=WEBMARKETTIMEMACHINEDTOWEBMARKETTIMEMACHINEGET_OPERATION, request_schema='WebMarketTimeMachineDtoWebMarketTimeMachineGetRequest', success_schema='WebMarketTimeMachineDtoWebMarketTimeMachineGetSuccess', error_schema='WebMarketTimeMachineDtoWebMarketTimeMachineGetError'),
    ContractRegistryEntry(registry_id='http:web_timeline_dto_web_timeline_get', source_head=SOURCE_HEAD, operation=WEBTIMELINEDTOWEBTIMELINEGET_OPERATION, request_schema='WebTimelineDtoWebTimelineGetRequest', success_schema='WebTimelineDtoWebTimelineGetSuccess', error_schema='WebTimelineDtoWebTimelineGetError'),
)
