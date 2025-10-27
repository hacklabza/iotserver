from django.utils import timezone


def aggregate_statuses(statuses):
    """
    Returns device stats by minimum, maximum and average values for today.
    """
    today = timezone.now().date()
    statuses = statuses.filter(created_at__date=today)

    aggregates = {}
    for status in statuses:
        for key, value in status.status.items():
            if isinstance(value, dict):
                if key not in aggregates:
                    aggregates[key] = {}
                for subkey, subvalue in value.items():
                    if subkey not in aggregates[key]:
                        aggregates[key][subkey] = {
                            'minimum': subvalue,
                            'maximum': subvalue
                        }
                    else:
                        aggregates[key][subkey]['minimum'] = min(
                            aggregates[key][subkey]['minimum'], subvalue
                        )
                        aggregates[key][subkey]['maximum'] = max(
                            aggregates[key][subkey]['maximum'], subvalue
                        )
                    aggregates[key][subkey]['average'] = (
                        aggregates[key][subkey]['minimum'] +
                        aggregates[key][subkey]['maximum']
                    ) / 2
            else:
                if key not in aggregates:
                    aggregates[key] = {'minimum': value, 'maximum': value}
                else:
                    aggregates[key]['minimum'] = min(aggregates[key]['minimum'], value)
                    aggregates[key]['maximum'] = max(aggregates[key]['maximum'], value)
                aggregates[key]['average'] = (
                    aggregates[key]['minimum'] + aggregates[key]['maximum']
                ) / 2
    return aggregates
