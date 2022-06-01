from app.application import reservation as mreservation, settings as msettings


false = False
true = True
null = None


def prepare_registration_form(code):
    ret = mreservation.prepare_reservation(code)
    if ret.result == ret.Result.E_OK:
        available_timeslots = ret.ret['available_timeslots']
        template = ret.ret['template']
        update_available_timeslots(available_timeslots, template, 'radio-timeslot')
        update_template(template, new='new' == ret.ret['mode'] )
    return ret


def prepare_settings_form(form):
    component = search_component(form, 'div-load-guest-file')
    template = msettings.get_configuration_setting('div-load-guest-file')
    component['html'] = template


def update_template(template, new):
    new_header = search_component(template, 'header-new')
    new_header['hidden'] = not new
    update_header = search_component(template, 'header-update')
    update_header['hidden'] = new
    child_name = search_component(template, 'child_name')
    child_name['disabled'] = not new
    email = search_component(template, 'email')
    email['disabled'] = not new
    # show_phone = msettings.get_configuration_setting('import-phone-field') != ''
    # phone = search_component(template, 'phone')
    # phone['hidden'] = not show_phone and not new
    show_name = msettings.get_configuration_setting('import-parentname-field') != ''
    parent_name = search_component(template, 'full_name')
    parent_name['hidden'] = not show_name and not new


def update_available_timeslots(timeslots, form, key):
    components = form['components']
    for component in components:
        if 'key' in component and component['key'] == key:
            values = []
            # component['components'] = []
            for timeslot in timeslots:
                if timeslot['available'] <= 0:
                    continue
                new = {
                    'label': timeslot['label'],
                    'value': timeslot['value'],
                    'shortcut': '',
                }
                values.append(new)
                if timeslot['default']:
                    component['defaultValue'] = timeslot['value']
            component['values'] = values
            return
        if 'components' in component:
            update_available_timeslots(timeslots, component, key)
    return





def search_component(form, key):
    components = form['components']
    for component in components:
        if 'key' in component and component['key'] == key:
            return component
        if 'components' in component:
            found_component = search_component(component, key)
            if found_component: return found_component
    return None


