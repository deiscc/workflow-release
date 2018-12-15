## Workflow ## {{pre_version}} -> {{version}}

#### Releases

{% for version in change_versions %}
- {{version[0]}} {{version[1]}} -> {{version[2]}}
{% endfor %}

{% for key, values in change_logs.items() %}

{% if key == "feat" %}
#### Features
{% elif key == "fix" %}
#### Fixes
{% elif key == "docs" %}
#### Docs
{% elif key == "test" %}
#### Test case
{% elif key == "chore" %}
#### Maintenance
{% else %}
#### {{ key|e|capitalize }}
{% endif %}

{% for value in values %}
- [`{{value["tree"]["sha"][:7]}}`]({{value["tree"]["url"]}}) ({{value["name"]}}) - {{value["message"]}}
{% endfor %}
{% endfor %}