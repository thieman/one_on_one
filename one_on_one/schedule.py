import httplib2
import datetime

from oauth2client.client import SignedJwtAssertionCredentials
from apiclient import discovery

class Schedule(object):
    def schedule(self, pairs, meeting_dt=None):
        """ This method is made to be overwritten by subclasses.
            It should take in a list of pairs, and schedule a meeting between
            the pairs of people
            meeting_dt is an optional datetime at which the meetings will start
        """
        raise NotImplementedError

class GCSchedule(Schedule):
    @staticmethod
    def get_credentials():
        client_email = 'one-on-one-account@windy-raceway-118617.iam.gserviceaccount.com'
        with open("ConvertedPrivateKey.pem") as f:
            private_key = f.read()
        credentials = SignedJwtAssertionCredentials(client_email,
                                                    private_key,
                                                    ['https://www.googleapis.com/auth/calendar',
                                                     'https://www.googleapis.com/auth/admin.directory.user.readonly'],
                                                     sub='kristin@gc.com')
        return credentials

    @staticmethod
    def get_gc_email(directory_access, full_name):
        split_names = full_name.split(' ')
        first_name = split_names[0]
        last_name = split_names[1]

        for name in [full_name, last_name, first_name]:
            results = directory_access.users().list(customer='my_customer', query="name:{}".format(name)).execute()
            if len(results.get('users', [])) == 1:
                return results['users'][0]['emails'][0]['address']

        raise KeyError("Cannot identify user from name: {}".format(full_name))

    def create_meeting(self, pair, meeting_start, meeting_end, calendar_access, directory_access):
        email_1 = self.get_gc_email(directory_access, pair[0])
        email_2 = self.get_gc_email(directory_access, pair[1])

        start_doc = {'date': meeting_start.split(' ')[0], 'timezone': 'America/New_York', 'datetime': meeting_start}
        end_doc = {'date': meeting_end.split(' ')[0], 'timezone': 'America/New_York', 'datetime': meeting_end}

        attendees = [{'email': email_1}, {'email': email_2}]

        body = {'attendees': attendees,
                'start': start_doc,
                'end': end_doc,
                'summary': 'Peer One on One: {} and {}'.format(pair[0], pair[1]),
                'description': 'This is a chance to meet and talk with someone else at GC. If you are not sure what to talk about, consult this link: http://jasonevanish.com/2014/05/29/101-questions-to-ask-in-1-on-1s/'}

        calendar_access.events().insert(calendarId='gamechanger.io_8ag52p72ocos9b61g7tcdt98ds@group.calendar.google.com',
                                        body=body,
                                        sendNotifications=True).execute()

    def schedule(self, pairs, meeting_dt=None):
        """
            This schedule function is built around Googles Api. Its goal is to schedule
            google calendar events for each set of pairs. To do this it uses the following
            api resources:
                Google Calendar: https://developers.google.com/google-apps/calendar/?hl=en
                Google Directory: https://developers.google.com/admin-sdk/directory/
            It also makes use of Google Service Accounts: https://developers.google.com/identity/protocols/OAuth2ServiceAccount
            If meeting_dt is not passed, assume that the meetings should be schedule a week from today at 10 a.m.
        """
        if meeting_dt is None:
            now = datetime.datetime.now()
            one_week_from_now = now + datetime.timedelta(7)
            meeting_start = str(datetime.datetime(one_week_from_now.year, one_week_from_now.month, one_week_from_now.day, 10, 30, 0))
            meeting_end = str(datetime.datetime(one_week_from_now.year, one_week_from_now.month, one_week_from_now.day, 11, 0, 0))
        else:
            meeting_start = str(meeting_dt)
            meeting_end = str(datetime.datetime(meeting_dt.year, meeting_dt.month, meeting_dt.day, meeting_dt.hour, meeting_dt.minute + 30, meeting_dt.second))
        credentials = self.get_credentials()
        http = credentials.authorize(httplib2.Http())
        calendar_access = discovery.build('calendar', 'v3', http=http)
        directory_access = discovery.build('admin', 'directory_v1', http=http)
        for pair in pairs:
            self.create_meeting(pair, meeting_start, meeting_end, calendar_access, directory_access)

