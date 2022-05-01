from enum import Enum

ROLES = ('Участник', 'Волонтёр', 'Сотрудник')

class Role(Enum):
    MEMBER = ROLES[0]  
    VOLUNTEER = ROLES[1]
    WORKER = ROLES[2]