import factory
from ckan import model
from ckan.plugins import toolkit
from ckantoolkit.tests import factories
from ckanext.api_tracking.models import TrackingUsage


class TrackingUsageF(factory.Factory):
    class Meta:
        model = TrackingUsage

    user_id = factory.LazyAttribute(lambda obj: factories.UserWithToken()['id'])
    # ui | api
    tracking_type = factory.Iterator(['ui', 'api'])
    # show | edit | home | download
    tracking_sub_type = factory.Iterator(['show', 'edit', 'home', 'download'])
    # get the token from the UserWithToken factory
    token_name = factory.Sequence(lambda n: "token-{0:05d}".format(n))
    # dataset | resource | organization
    object_type = factory.Iterator(['dataset', 'resource', 'organization'])
    object_id = factory.Sequence(lambda n: "object-id-{0:05d}".format(n))
    # More information about the usage
    extras = {}

    # allow defining user_id and token name from an user dict
    @factory.post_generation
    def user(self, create, extracted, **kwargs):
        if extracted:
            self.user_id = extracted['id']
            user_obj = model.User.get(self.user_id)
            token_name = f'token-{user_obj.name}'
            self.token_name = token_name

            # Check if the token already exists in DB
            token = model.Session.query(model.ApiToken).filter_by(name=token_name).first()
            if token:
                return

            # Create the token
            token_data = {"user": user_obj.name, "name": token_name}
            toolkit.get_action(u"api_token_create")({"ignore_auth": True}, token_data)

    @classmethod
    def _create(cls, target_class, *args, **kwargs):
        obj = target_class(**kwargs)
        model.Session.add(obj)
        model.Session.commit()
        model.Session.remove()

        return obj


class TrackingUsageUIDataset(TrackingUsageF):
    tracking_type = 'ui'
    tracking_sub_type = 'show'
    object_type = 'dataset'


class TrackingUsageUIDatasetEdit(TrackingUsageF):
    tracking_type = 'ui'
    tracking_sub_type = 'edit'
    object_type = 'dataset'


class TrackingUsageUIDatasetHome(TrackingUsageF):
    tracking_type = 'ui'
    tracking_sub_type = 'home'
    object_type = 'dataset'


class TrackingUsageUIResourceDownload(TrackingUsageF):
    tracking_type = 'ui'
    tracking_sub_type = 'download'
    object_type = 'resource'


class TrackingUsageAPIDataset(TrackingUsageF):
    tracking_type = 'api'
    tracking_sub_type = 'show'
    object_type = 'dataset'


class TrackingUsageAPIResource(TrackingUsageF):
    tracking_type = 'api'
    tracking_sub_type = 'show'
    object_type = 'resource'


class TrackingUsageAPIResourceDownload(TrackingUsageF):
    tracking_type = 'api'
    tracking_sub_type = 'download'
    object_type = 'resource'
