from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.schemas import Schemas
from opentelemetry.semconv._incubating.attributes import deployment_attributes, service_attributes

DEFAULT_NAMESPACE = "default"
DEFAULT_VERSION = "0.1.0"
DEFAULT_SERVICE_NAME = "default"


class ResourceBuilder:
    def __init__(self):
        self.attributes = {
            service_attributes.SERVICE_NAME:      DEFAULT_SERVICE_NAME,
            service_attributes.SERVICE_NAMESPACE: DEFAULT_NAMESPACE,
            service_attributes.SERVICE_VERSION:   DEFAULT_VERSION,
        }
        self.schema_url = Schemas.V1_38_0

    @classmethod
    def new(cls) -> 'ResourceBuilder':
        return cls()

    def with_version(self, version: str) -> 'ResourceBuilder':
        self.attributes[service_attributes.SERVICE_VERSION] = version
        return self

    def with_name(self, name: str) -> 'ResourceBuilder':
        self.attributes[service_attributes.SERVICE_NAME] = name
        return self

    def with_namespace(self, namespace: str) -> 'ResourceBuilder':
        self.attributes[service_attributes.SERVICE_NAMESPACE] = namespace
        return self

    def with_environment(self, environment: str) -> 'ResourceBuilder':
        self.attributes[deployment_attributes.DEPLOYMENT_ENVIRONMENT] = environment
        return self

    def with_custom_attribute(self, key: str, value: str) -> 'ResourceBuilder':
        self.attributes[key] = value
        return self

    def build(self) -> Resource:
        return Resource.create(self.attributes, schema_url=self.schema_url.value)
