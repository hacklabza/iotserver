from django.utils import timezone


def aggregate_statuses(statuses: list[dict]) -> dict:
    """
    Returns device stats by minimum, maximum and average values for today.
    """
    today = timezone.now().date()
    statuses = statuses.filter(created_at__date=today)

    aggregates = {}
    values_for_avg = {}

    for status in statuses:
        for key, value in status.status.items():
            if isinstance(value, dict):
                if key not in aggregates:
                    aggregates[key] = {}
                    values_for_avg[key] = {}
                for subkey, subvalue in value.items():
                    if subkey not in aggregates[key]:
                        aggregates[key][subkey] = {
                            'minimum': subvalue,
                            'maximum': subvalue
                        }
                        values_for_avg[key][subkey] = [subvalue]
                    else:
                        aggregates[key][subkey]['minimum'] = min(
                            aggregates[key][subkey]['minimum'], subvalue
                        )
                        aggregates[key][subkey]['maximum'] = max(
                            aggregates[key][subkey]['maximum'], subvalue
                        )
                        values_for_avg[key][subkey].append(subvalue)
                    aggregates[key][subkey]['average'] = (
                        sum(values_for_avg[key][subkey]) / len(values_for_avg[key][subkey])
                    )
            else:
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    continue
                if key not in aggregates:
                    aggregates[key] = {'minimum': value, 'maximum': value}
                    values_for_avg[key] = [value]
                else:
                    aggregates[key]['minimum'] = min(aggregates[key]['minimum'], value)
                    aggregates[key]['maximum'] = max(aggregates[key]['maximum'], value)
                    values_for_avg[key].append(value)
                aggregates[key]['average'] = sum(values_for_avg[key]) / len(values_for_avg[key])

    return aggregates
