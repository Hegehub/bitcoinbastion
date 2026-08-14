from __future__ import annotations

import httpx
import reflex as rx

from bastion_ui.config import get_config
from bastion_ui.domain.lifecycle import LifecycleStatus, project_transport_error
from bastion_ui.domain.operations.adapters import (
    adapt_health,
    adapt_incidents,
    adapt_operations_slo,
    adapt_providers,
    adapt_storage,
)
from bastion_ui.domain.operations.models import (
    HealthViewModel,
    IncidentsViewModel,
    OperationsSLOListViewModel,
    ProvidersViewModel,
    StorageViewModel,
)
from bastion_ui.transport.foundation import HttpTransport, SafeTransportError
from bastion_ui.transport.generated_http import (
    HealthApiV1HealthGetRequest,
    OperationsListIncidentsRequest,
    OperationsListSloRequest,
    ProvidersApiV1HealthProvidersGetRequest,
    StorageStatusApiV1StorageStatusGetRequest,
    health_api_v1_health_get,
    operations_list_incidents,
    operations_list_slo,
    providers_api_v1_health_providers_get,
    storage_status_api_v1_storage_status_get,
)


class HealthState(rx.State):
    value: HealthViewModel | None = None
    lifecycle: str = LifecycleStatus.IDLE.value
    safe_error: str = ""
    generation: int = 0

    async def load(self) -> None:
        self.generation += 1
        token = self.generation
        self.lifecycle = LifecycleStatus.LOADING.value
        self.safe_error = ""
        config = get_config()
        try:
            async with httpx.AsyncClient(base_url=config.api_base_url) as client:
                response = await health_api_v1_health_get(
                    HttpTransport(client, timeout_seconds=config.request_timeout_seconds),
                    HealthApiV1HealthGetRequest(),
                )
            if token != self.generation:
                return
            self.value = adapt_health(response)
            self.lifecycle = LifecycleStatus.SUCCESS.value
        except SafeTransportError as error:
            if token == self.generation:
                status, safe = project_transport_error(error)
                self.lifecycle, self.safe_error = status.value, safe.summary

    def invalidate(self) -> None:
        self.generation += 1


class ProvidersState(rx.State):
    value: ProvidersViewModel | None = None
    lifecycle: str = LifecycleStatus.IDLE.value
    safe_error: str = ""
    generation: int = 0

    async def load(self) -> None:
        self.generation += 1
        token = self.generation
        self.lifecycle = LifecycleStatus.LOADING.value
        self.safe_error = ""
        config = get_config()
        try:
            async with httpx.AsyncClient(base_url=config.api_base_url) as client:
                response = await providers_api_v1_health_providers_get(
                    HttpTransport(client, timeout_seconds=config.request_timeout_seconds),
                    ProvidersApiV1HealthProvidersGetRequest(),
                )
            if token != self.generation:
                return
            self.value = adapt_providers(response)
            self.lifecycle = (
                LifecycleStatus.EMPTY.value
                if not self.value.providers
                else LifecycleStatus.SUCCESS.value
            )
        except SafeTransportError as error:
            if token == self.generation:
                status, safe = project_transport_error(error)
                self.lifecycle, self.safe_error = status.value, safe.summary

    def invalidate(self) -> None:
        self.generation += 1


class StorageState(rx.State):
    value: StorageViewModel | None = None
    lifecycle: str = LifecycleStatus.IDLE.value
    safe_error: str = ""
    generation: int = 0

    async def load(self) -> None:
        self.generation += 1
        token = self.generation
        self.lifecycle = LifecycleStatus.LOADING.value
        self.safe_error = ""
        config = get_config()
        try:
            async with httpx.AsyncClient(base_url=config.api_base_url) as client:
                response = await storage_status_api_v1_storage_status_get(
                    HttpTransport(client, timeout_seconds=config.request_timeout_seconds),
                    StorageStatusApiV1StorageStatusGetRequest(),
                )
            if token != self.generation:
                return
            self.value = adapt_storage(response)
            self.lifecycle = LifecycleStatus.SUCCESS.value
        except SafeTransportError as error:
            if token == self.generation:
                status, safe = project_transport_error(error)
                self.lifecycle, self.safe_error = status.value, safe.summary

    def invalidate(self) -> None:
        self.generation += 1


class IncidentsState(rx.State):
    value: IncidentsViewModel | None = None
    lifecycle: str = LifecycleStatus.IDLE.value
    safe_error: str = ""
    generation: int = 0

    async def load(self) -> None:
        self.generation += 1
        token = self.generation
        self.lifecycle = LifecycleStatus.LOADING.value
        self.safe_error = ""
        config = get_config()
        try:
            async with httpx.AsyncClient(base_url=config.api_base_url) as client:
                response = await operations_list_incidents(
                    HttpTransport(client, timeout_seconds=config.request_timeout_seconds),
                    OperationsListIncidentsRequest(),
                )
            if token != self.generation:
                return
            self.value = adapt_incidents(response)
            self.lifecycle = (
                LifecycleStatus.EMPTY.value
                if not self.value.incidents
                else LifecycleStatus.SUCCESS.value
            )
        except SafeTransportError as error:
            if token == self.generation:
                status, safe = project_transport_error(error)
                self.lifecycle, self.safe_error = status.value, safe.summary

    def invalidate(self) -> None:
        self.generation += 1


class OperationsSLOState(rx.State):
    value: OperationsSLOListViewModel | None = None
    lifecycle: str = LifecycleStatus.IDLE.value
    safe_error: str = ""
    generation: int = 0

    async def load(self) -> None:
        self.generation += 1
        token = self.generation
        self.lifecycle = LifecycleStatus.LOADING.value
        self.safe_error = ""
        config = get_config()
        try:
            async with httpx.AsyncClient(base_url=config.api_base_url) as client:
                response = await operations_list_slo(
                    HttpTransport(client, timeout_seconds=config.request_timeout_seconds),
                    OperationsListSloRequest(),
                )
            if token != self.generation:
                return
            self.value = adapt_operations_slo(response)
            self.lifecycle = (
                LifecycleStatus.EMPTY.value
                if not self.value.objectives
                else LifecycleStatus.SUCCESS.value
            )
        except SafeTransportError as error:
            if token == self.generation:
                status, safe = project_transport_error(error)
                self.lifecycle, self.safe_error = status.value, safe.summary

    def invalidate(self) -> None:
        self.generation += 1
