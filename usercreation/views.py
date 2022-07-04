from django.shortcuts import render
from general.models import Roles, Users, Contacts
import general.db_func as dbf
from datetime import datetime
import general.main_func as mf

def adduserform(request):
    allroles = Roles.objects.all()   

    # roles_list = [f'{i.id}|{i.role}'for i in allroles]
    roles_list = [i for i in allroles]

    context = {
        'roles_list': roles_list
    }

    # for i in allroles:
    #     roles_list.append(i.role)


    # context = {
    #     'member': allroles[0].role,
    #     'volunteur': allroles[1].role,
    #     'worker': allroles[2].role
    # }

    return render(request, "usercreation/adduserform.html", context)


def results(request):
    if request.method == 'POST':
        data = request.POST

        user = {
            'role': Roles.objects.get(id=int(data['role'].split(' ')[0])),
            'date': datetime.now().date(),
            'qrc_status': False,
            'note': data['note'],
            'expire': data['expire'],
            'vv_card': data['vvcard'],
            'name': data['name'],
            'email': data['email'],
            'phone': mf.correct_phone_number(data['phone'])
        }

        unique_user = {'email': True, 'phone': True, 'vvcard': True}

        if Contacts.objects.filter(elmail=user['email']).exists():
            unique_user['email'] = False
        
        if Contacts.objects.filter(phone=user['phone']).exists():
            unique_user['phone'] = False

        if Users.objects.filter(vvcard=user['vv_card']).exists():
            unique_user['vvcard'] = False
                

        if False in unique_user.values():                        
            status = f'Пользователь не уникален: {[f"{k}: {unique_user[k]}" for k in unique_user]}'
            last_user = None
        else:
            dbf.add_user(user, db_fill=False)

            last_user = Contacts.objects.select_related('user').last()
            status = 'Добавлено успешно'

        context = {
            'status': status,
            'last_user': last_user
        }


    return render(request, "usercreation/addition_result.html", context)

