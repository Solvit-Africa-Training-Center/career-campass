

## Testing our API
---
To run the tests, use the following commands:

First, set the DJANGO_SETTINGS_MODULE environment variable:

```bash
export DJANGO_SETTINGS_MODULE=core.settings
```
```windows
set DJANGO_SETTINGS_MODULE=core.settings
```

Then run:

```bash
pytest
```

**Note:**  
You may see a warning like:
```
RuntimeWarning: Model 'catalog.programfee' was already registered. Reloading models is not advised as it can lead to inconsistencies, most notably with related models.
```
This warning can be ignored if all tests pass.