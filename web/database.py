from bson.objectid import ObjectId


def get_area_by_levels(db, election_id, country_id,
                       level1_val, level2_val, level3_val,
                       level1_opt, level2_opt, level3_opt, statistic_mode=False):

    if level3_val is not None and len(level3_val) > 0 and any(d['value'] == level3_val[0] for d in level3_opt):
        max_zoom_opt = level3_opt
        max_zoom_area = level3_val
    elif level2_val is not None and len(level2_val) > 0 and any(d['value'] == level2_val[0] for d in level2_opt):
        max_zoom_opt = level2_opt
        max_zoom_area = level2_val
    elif level1_val is not None and len(level1_val) > 0 and any(d['value'] == level1_val[0] for d in level1_opt):
        max_zoom_opt = level1_opt
        max_zoom_area = level1_val
    else:
        max_zoom_opt = level1_val
        max_zoom_area = [country_id]

    parent_ids = []
    # Если в максимальном указанном приближении указан пункт ALL вместо конкретной территории
    if max_zoom_area is not None and 'all' in max_zoom_area:
        for i, a in enumerate(max_zoom_opt):
            if a['value'] != 'all' and type(a['value']) is str:
                parent_ids.append(ObjectId(a['value']))
    else:
        for i, a in enumerate(max_zoom_area):
            if a == 'all':
                continue
            if type(a) is str:
                parent_ids.append(ObjectId(a))
            elif type(a) is ObjectId:
                parent_ids.append(ObjectId(a))

    where = {'results_tags': election_id}
    fields = {'results.' + election_id: True}
    if statistic_mode:
        where['_id'] = {'$in': parent_ids}
    else:
        where['parent_id'] = {'$in': parent_ids}
        fields['num'] = True
        fields['name'] = True
        fields['address'] = True

    ret = db.area.find(where, fields)
    return ret
