import re

def parse_mailfunction_api(text: str):
    result = {}
    data_list = []
    current_item = None
    in_data = False

    def parse_value(val):
        val = val.strip()
        m = re.match(r'^"(.*)"$', val)
        if m:
            return m.group(1)
        if re.fullmatch(r'\d+', val):
            return int(val)
        if re.fullmatch(r'\d+\.\d+', val):
            return float(val)
        return val

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if not in_data:
            if line == "data":
                in_data = True
                continue
            key_val = line.split(None, 1)
            if key_val:
                key = key_val[0]
                if len(key_val) == 2:
                    val = parse_value(key_val[1])
                    result[key] = val
                continue

        if re.fullmatch(r'\d+', line):
            if current_item is not None:
                data_list.append(current_item)
            current_item = {}
        else:
            parts = line.split(None, 1)
            if len(parts) == 2:
                key, raw_val = parts
                current_item[key] = parse_value(raw_val)

    if current_item is not None:
        data_list.append(current_item)

    result["data"] = data_list
    return result
