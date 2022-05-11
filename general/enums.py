from enum import Enum

ROLES = ('Сотрудник', 'Волонтёр', 'Участник')

class Role(Enum):
    MEMBER = ROLES[0]  
    VOLUNTEER = ROLES[1]
    WORKER = ROLES[2]