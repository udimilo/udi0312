import logic
import cacher

def index():
    return dict(boards=[], categories=[])

def linkedin():
    if not session.verified: redirect(URL('default', 'index'))

    current_user = cacher.get('auth_user', auth.user.id)

    connections = session.linkedin.get_connections(fields=['id', 'first-name', 'last-name','picture-url'])

    un = [c.id for c in connections]
    users = logic.get_users_by_username(un)

    in_users = []
    out_users = []

    for c in connections:
        if c.picture_url is None:
            c.picture_url = 'http://static02.linkedin.com/scds/common/u/img/icon/icon_no_photo_60x60.png'

        if users.has_key(c.id):
            u = users[c.id]
            is_following = any(u['id'] == id for id in current_user['follow_users'])
            if is_following:
                c.action = 'unfollow'
            else:
                c.action = 'follow'

            # move it to the else if we want to eliminate already followed people
            c.user_id = u['id']
            in_users.append(c)
        else:
            out_users.append(c)



    return dict(in_users=in_users, out_users=out_users)