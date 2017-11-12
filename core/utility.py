from django.core.mail import send_mail
from django.utils import timezone as django_timezone
from django.db import IntegrityError
from django.utils.dateparse import parse_datetime
from django.urls import reverse
from tutoriabeta import settings
from pytz import timezone
from datetime import datetime, timedelta
from .models import *
import random
import string


# datetime related function

def toLocalDatetime(date):
    local_timezone = timezone(settings.TIME_ZONE)
    return date.astimezone(local_timezone)

def getCurrentDatetime():
    local_timezone = timezone(settings.TIME_ZONE)
    return datetime.now().astimezone(local_timezone)

def getTimeStr(date):
    local_timezone = timezone(settings.TIME_ZONE)
    return date.astimezone(local_timezone).strftime('%H:%M')

def getDatetimeStr(date):
    local_timezone = timezone(settings.TIME_ZONE)
    return date.astimezone(local_timezone).strftime('%Y-%m-%d %H:%M')

def getDateStr(date):
    local_timezone = timezone(settings.TIME_ZONE)
    return date.astimezone(local_timezone).strftime('%Y-%m-%d')

def getDatetimeStr2(date):
    local_timezone = timezone(settings.TIME_ZONE)
    return date.astimezone(local_timezone).strftime('%e %b %Y, %H:%M')

def getDateStr2(date):
    local_timezone = timezone(settings.TIME_ZONE)
    return date.astimezone(local_timezone).strftime('%e %b %Y')

def getNextHalfHour(date):
    delta = timedelta(minutes=30)
    return date + (datetime.min - date) % delta

def getNearestHalfHour(date):
    ceiling = getNextHalfHour(date)
    if date > date.replace(minute=30,second=0, microsecond=0):
        floor = date.replace(minute=30,second=0, microsecond=0)
    else:
        floor = date.replace(minute=0,second=0, microsecond=0)
    if date - floor <= ceiling - date:
        return floor
    else:
        return ceiling


# other function that do not want to put in views
def sendEmailToTutor(s):
    msg_body = 'Dear '+s.tutor.profile.user.username+",\n"+\
               'Student with username <'+s.student.profile.user.username+ '>'+\
               ' has booked a session with you at '+s.getBookingDateStr+ ".\n" + \
               'The session will start at ' +s.getBookedDateStr+ ' from ' +s.getStartTimeStr+ ' to ' + s.getEndTimeStr+'.\n'\
               'The contact number of the student is '+s.student.profile.phone+"."

    send_mail(
        'You have a new session booked',
        msg_body,
        'noreplay@tutoria.com',
        [s.tutor.profile.user.email],
        fail_silently=False,
        )

def sendBookingNotification(s, credited_amount):
    isPrivateTutor = s.tutor.isPrivateTutor

    now = getCurrentDatetime()

    amount = '%.2f'%credited_amount
    #for student
    student_msg =   'Dear '+s.student.profile.user.username+\
                    ',\nYou have successfully booked a session with tutor '+s.tutor.profile.user.username+\
                    ' at '+s.getBookingDateStr+'.\n'+\
                    'The session will start at ' +s.getBookedDateStr+ ' from ' +s.getStartTimeStr+ ' to ' + s.getEndTimeStr+'.\n\n'\
                    'Please remind that, you will not able to cancel the booked session at the time that the session is about to start within 24 hour.\n'
    if isPrivateTutor:
        student_msg += '\nSince you have booked a private tutor, '+\
                        'HKD '+amount+' has been deducted from your wallet. '+\
                        'This amount will be refunded if you cancel the session at less 24 hour before the starting time of the session.\n'

    s_n = Notification(profile = s.student.profile, message = student_msg, date=now)
    s_n.save()

    #for tutor
    tutor_msg = 'Dear '+s.tutor.profile.user.username+",\n"+\
                'Student with username '+s.student.profile.user.username+ \
                ' has booked a session with you at '+s.getBookingDateStr+ ".\n" + \
                'The session will start at ' +s.getBookedDateStr+ ' from ' +s.getStartTimeStr+ ' to ' + s.getEndTimeStr+'.\n'\
                'The contact number of the student is '+s.student.profile.phone+"."
    
    if isPrivateTutor:
        student_msg += 'HKD '+amount+' will be transer to your wallet, '+\
                        'if the session has not been cancelled at less 24 hour before the starting time of the session.\n'

    t_n = Notification(profile = s.tutor.profile, message = tutor_msg, date=now)
    t_n.save()

def sendTutorPaymentNotification(s):
    now = getCurrentDatetime()

    #for tutor
    tutor_msg = 'Dear '+s.tutor.profile.user.username+",\n"+\
                'Since your tutorial session with the student '+s.student.profile.user.username+' has began.\n' +\
                'The tutor fee HKD '+'%.2f'%s.tutor.hourly_rate+" has been transfered to your wallet."

    t_n = Notification(profile = s.tutor.profile, message = tutor_msg, date=now)
    t_n.save()

def validateBookingDatetime(date_start, date_end, tutor):
    if date_start < getCurrentDatetime()+timedelta(hours=24):
        return False
    session_list = Session.objects.filter(tutor=tutor).exclude(end_date__lte = date_start).exclude(start_date__gte=date_end)
    if len(session_list)>0:
        return False
    else:
        return True

def checkFairBook(date_start, date_end, tutor, student):
    session_list = Session.objects.filter(tutor=tutor).filter(isBlackedout=False).filter(student=student).filter(start_date__date=date_start.date())
    if len(session_list)>0:
        return False
    else:
        return True

def checkNext7day(tutor):
    hasTimeslot = False
    date = getNextHalfHour(datetime.now())
    end_date = date + timedelta(days=6)
    end_date = end_date.replace(hour=18,minute=30,second=00)
    while date <= end_date:
        if date > date.replace(hour=18,minute=30,second=00):
            date += timedelta(days=1)
            date = date.replace(hour=8,minute=30,second=00)
        if tutor.isPrivateTutor:
            hasTimeslot = validateBookingDatetime(toLocalDatetime(date), toLocalDatetime(date+timedelta(hours=1)), tutor)
        else:
            hasTimeslot = validateBookingDatetime(toLocalDatetime(date), toLocalDatetime(date+timedelta(minutes=30)), tutor)
        if hasTimeslot:
            return True

        date += timedelta(minutes=30)
    
    return False

def reviewInvitation(s):
    expire_date = getCurrentDatetime() + timedelta(days=3)
    success = False
    while not success:
        try:
            url_str = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(32))
            u = ReviewTempUrl(temp_url=url_str, tutor=s.tutor, student=s.student, expires=expire_date)
            u.save()
            success = True
        except IntegrityError:
            pass
    web_domain = "http://127.0.0.1:8000"
    msg = "Dear {0}, you have finished a session with tutor {1}.\n Thanks for using Tutoria, we sincerely invite you to leave a review for tutor {1}, please click the link below to enter the review page. Note that the link will expire 3 days after.\n\n<a href=\"{2}{3}\">click me to visit review page</a>".format(s.student.profile.getUsername, s.tutor.profile.getUserFullName, web_domain ,reverse('review_tutor', args=(url_str,)))

    s_n = Notification(profile = s.student.profile, message = msg, date=getCurrentDatetime())
    s_n.save()