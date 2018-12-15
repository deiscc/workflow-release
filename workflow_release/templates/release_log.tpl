### {{pre_version}} -> {{version}}

{% for key, values in commits.items() %}

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
- [`{{value["tree"]["sha"][:7]}}`]({{value["tree"]["url"]}}) {{value["message"]}}
{% endfor %}
{% endfor %}