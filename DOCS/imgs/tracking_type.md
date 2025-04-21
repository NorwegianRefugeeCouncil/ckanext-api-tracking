# Tracking type values

The `tracking_type` field indicates the general channel through which a user is interacting with CKAN.  
This is a open field, these are only suggestions.  

Available `tracking_type`s are:  

| Value | Description | Example |
|-------|-------------|---------|
| `api` | The user accessed CKAN through the API | `/api/3/action/package_show?id=dataset-name` |
| `ui` | The user accessed CKAN through the web interface | `/dataset/dataset-name` |

## Tracking Sub-Type Values

The `tracking_sub_type` field provides more detail about what kind of action was performed.  

| Value | Description | Associated With | Example |
|-------|-------------|----------------|---------|
| `show` | Viewing an entity | api, ui | Viewing a dataset page, calling package_show |
| `edit` | Modifying an entity | api, ui | Updating a resource, calling package_update |
| `home` | Viewing an index/listing page | ui | Viewing the dataset search page |
| `login` | User login event | user | User logs in via the UI |
| `logout` | User logout event | user | User logs out via the UI |
| `download` | Resource download | ui | User downloads a resource file |

## Object Type Values

The `object_type` field identifies the type of CKAN entity being interacted with.  

| Value | Description |
|-------|-------------|
| `dataset` | A CKAN dataset (package) |
| `resource` | A resource within a dataset |
| `organization` | A CKAN organization |
| `user` | A CKAN user |

## Extras

The `extras` field is a JSON object that contains additional information about the interaction.  

We use extras to:
 - Store the HTTP method (GET, POST, etc.) used in the request

And it could be eventually used to:
 - Track API version information for API calls
 - Store query parameters that might be relevant for analysis
 - Record additional context about user actions (like referrer URL)
 - Capture error information when tracking failed API requests
 - Record the user agent and client information
 - Store performance metrics (response time, etc.)
