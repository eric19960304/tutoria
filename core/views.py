from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from .forms import SignUpForm
from .models import *
from tutoriabeta import settings
from datetime import datetime, timedelta
from django.utils.dateparse import parse_datetime
from django.db.models import Q
from .handleTransaction import *
from .factory import initDatabase, createUser
from .utility import *
from decimal import Decimal
from collections import Counter

@login_required
def adminCoupon(request):
    if request.POST:
        if 'amount' in request.POST and 'expire_date' in request.POST and request.POST['amount']!="" and request.POST['expire_date']!="":
            amount = int(request.POST['amount'])
            expire_date = toLocalDatetime(parse_datetime(request.POST['expire_date']))
            for x in range(0, amount):
                success = False
                while not success:
                    try:
                        code = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(12))
                        c = Coupon(code=code, expire_date=expire_date)
                        c.save()
                        success = True
                    except IntegrityError:
                        pass
            msg="{} coupon is successfully generated.".format(amount)
            coupon_list = [ c for c in Coupon.objects.order_by('expire_date') if c.validate]
            context = {'coupon_list': coupon_list,'msg':msg}
            return render(request, 'admin_coupon.html', context)
        else:
            coupon_list = [ c for c in Coupon.objects.order_by('expire_date') if c.validate]
            context = {'coupon_list': coupon_list, 'msg':"Please enter the amount and expire date."}
            return render(request, 'admin_coupon.html', context)

    else:
        coupon_list = [ c for c in Coupon.objects.order_by("expire_date") if c.validate]
        context = {'coupon_list': coupon_list}
        return render(request, 'admin_coupon.html', context)

@login_required
def checkNotification(request):
    if request.GET:
        if 'id' in request.GET:
            id = int(request.GET['id'])
            n = Notification.objects.get(pk=id)
            n.checked=True
            n.save()
            return HttpResponse("Successful")
        else:
            return HttpResponse("Unsuccessful")
    else:
        return HttpResponse("Unsuccessful")


@login_required
def adminDrawFromWallet(request):
    user=request.user
    if user.username!="admin":
        request.session['title'] = "Restricted Access: admin only"
        request.session['message'] = "Restricted Access: admin only"
        return HttpResponseRedirect(reverse('message'))

    if not request.POST:
        return render(request, 'admin_draw_from_wallet.html')
    else:
        if 'amount' in request.POST:
            try:
                amount = float(request.POST['amount'])
            except:
                return render(request, 'admin_draw_from_wallet.html',{'msg':"Invalid input"})

            adminDrawFromTutoriaWallet(amount)

            request.session['title'] = "Transfer success"
            request.session['message'] = "HKD {} has transfered to Tutoria bank account.".format("%.2f"%amount)
            return HttpResponseRedirect(reverse('message'))
        else:
            return render(request, 'admin_draw_from_wallet.html')

@login_required
def adminWallet(request):
    user = request.user
    if user.username!="admin":
        request.session['title'] = "Restricted Access: admin only"
        request.session['message'] = "Restricted Access: admin only"
        return HttpResponseRedirect(reverse('message'))


    s = System.objects.all()[0]
    wallet = s.wallet

    current = getCurrentDatetime()
    monthBefore = current - timedelta(days=30)
    transactionHistory = Transaction.objects.filter(isTutoriaOwned=True).filter(date__gte = monthBefore).order_by("-date")

    context={'amount':wallet.amount, 'transactionHistory':transactionHistory}
    return render(request, 'admin_wallet.html', context)

@login_required
def addToWallet(request):
    user= request.user
    if not user.profile.isStudent:
        request.session['title'] = "Restricted Access"
        request.session['message'] = "Restricted Access"
        return HttpResponseRedirect(reverse('message'))

    if not request.POST:
        return render(request, 'add_to_wallet.html')
    else:
        if 'amount' in request.POST:
            try:
                amount = float(request.POST['amount'])
            except:
                return render(request, 'add_to_wallet.html',{'msg':"Invalid input"})

            studentAddToWallet(user.profile, amount)

            request.session['title'] = "Topup success"
            request.session['message'] = "HKD {} has added to your wallet.".format("%.2f"%amount)
            return HttpResponseRedirect(reverse('message'))
        else:
            return render(request, 'add_to_wallet.html')

@login_required
def drawFromWallet(request):
    user= request.user
    if not user.profile.isTutor:
        request.session['title'] = "Restricted Access"
        request.session['message'] = "Restricted Access"
        return HttpResponseRedirect(reverse('message'))

    if not request.POST:
        return render(request, 'draw_from_wallet.html')
    else:
        if 'amount' in request.POST:
            try:
                amount = float(request.POST['amount'])
            except:
                return render(request, 'draw_from_wallet.html',{'msg':"Invalid input"})

            tutorDrawFromWallet(user.profile, amount)

            request.session['title'] = "Transfer success"
            request.session['message'] = "HKD {} has transfered to your bank account.".format("%.2f"%amount)
            return HttpResponseRedirect(reverse('message'))
        else:
            return render(request, 'draw_from_wallet.html')

@login_required
def changePassword(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            return render(request, 'change_password.html', {'form': form, 'msg': "Your password was successfully updated!\n"})
        else:
            return render(request, 'change_password.html', {'form': form, 'msg': "Please correct the error below!\n"})
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'change_password.html', {'form': form})

@login_required
def editProfile(request):
    
    user = request.user

    if user.profile.isTutor:
        s_tag = user.profile.tutor.tag.all()
        s_course = user.profile.tutor.course.all()
        tag = Tag.objects.all()
        course = Course.objects.all()
        university = University.objects.all()
    
    if not request.POST:
        if user.profile.isTutor:
            t = user.profile.tutor
            context = {'tag': tag, 'course': course, 'university': university , 's_tag':s_tag, 's_course':s_course, 's_bio': t.bio, 'hide': t.isHideProfile,'isPrivateTutor':t.isPrivateTutor,'s_uni_abbrev': t.university.abbrev, 's_hourly_rate': t.hourly_rate}
        else:
            context = {}
        return render(request, 'edit_profile.html', context)
    else:
        changeFlag = False
        msg = ""
        
        if 'first_name' in request.POST and request.POST['first_name']!=user.first_name:
            user.first_name =  request.POST['first_name']
            user.save()
            changeFlag = True
            msg += "First name has been changed.\n"
        if 'last_name' in request.POST and request.POST['last_name']!=user.last_name:
            user.last_name =  request.POST['last_name']
            user.save()
            changeFlag = True
            msg += "Last name has been changed.\n"
        if 'email' in request.POST and request.POST['email']!=user.email:
            user.email =  request.POST['email']
            user.save()
            changeFlag = True
            msg += "Email has been changed.\n"
        
        if user.profile.tutor.getTutorType=="": #tutor type not selected
            t = Tutor.objects.filter(profile=user.profile)[0]
            if 'tutor_type' in request.POST:
                tutortype = TutorType.objects.filter(tutor_type=request.POST['tutor_type'])[0]
                t.tutor_type = tutortype
                t.save()
                msg += "Tutor type has been changed.\n"
                changeFlag = True
            

        elif user.profile.isTutor:
            t = Tutor.objects.filter(profile=user.profile)[0]
            
            if 'bio' in request.POST and request.POST['bio']!=user.profile.tutor.bio:
                t.bio = request.POST['bio']
                t.save()
                msg += "Bio has been changed.\n"
                changeFlag = True

            if 'university' in request.POST and request.POST['university']!=user.profile.tutor.university.abbrev:
                u = University.objects.filter(abbrev=request.POST['university'])[0]
                t.university = u
                t.save()
                msg += "University has been changed.\n"
                changeFlag = True
            
            if 'hourly_rate' in request.POST and request.POST['hourly_rate']!=user.profile.tutor.hourly_rate:
                t.hourly_rate = Decimal(request.POST['hourly_rate'])
                t.save()
                msg += "Hourly rate has been changed.\n"
                changeFlag = True

            if 'tutor_type' in request.POST and request.POST['tutor_type']!=t.getTutorType:
                tutortype = TutorType.objects.filter(tutor_type=request.POST['tutor_type'])[0]
                t.tutor_type = tutortype
                if request.POST['tutor_type']=="contracted":
                    t.hourly_rate = Decimal(0)
                t.save()
                msg += "Tutor type has been changed.\n"
                changeFlag = True
                
            if 'course' in request.POST:
                course_list = request.POST.getlist('course')
                course_code_list = [c.code for c in s_course]
                if Counter(course_code_list)!=Counter(course_list): # check if 2 lists contain same content
                    t.course.clear()
                    for each in course_list:
                        c = Course.objects.filter(code=each)[0]
                        t.course.add(c)
                    t.save()
                    msg += "Courses has been changed.\n"
                    changeFlag = True
            if 'tag' in request.POST:
                tag_list = request.POST.getlist('tag')
                tag_name_list = [t.name for t in s_tag]
                if Counter(tag_name_list)!=Counter(tag_list): # check if 2 lists contain same content
                    t.tag.clear()
                    for each in tag_list:
                        ta = Tag.objects.filter(name=each)[0]
                        t.tag.add(ta)
                    t.save()
                    msg += "Tags has been changed.\n"
                    changeFlag = True
            
            # check if hide profile
            choice = False
            if 'hide' in request.POST:
                choice = True
            if choice != t.isHideProfile:
                t.isHideProfile = choice
                t.save()
                msg += "Visibility of profile option has been changed.\n"
                changeFlag = True

        if not changeFlag:
            msg = "No change has made."

        if user.profile.isTutor:
            s_tag = Tag.objects.filter(tutor=user.profile.tutor)
            s_course = Course.objects.filter(tutor=user.profile.tutor)
            tag = Tag.objects.all()
            course = Course.objects.all()
            university = University.objects.all()
            s_bio = Tutor.objects.filter(profile=user.profile)[0].bio
            s_hide = Tutor.objects.filter(profile=user.profile)[0].isHideProfile
            context = {'tag': tag, 'course': course, 'university': university , 's_tag':s_tag, 's_course':s_course, 's_bio': s_bio,'hide':s_hide ,'msg':msg,'isPrivateTutor': t.isPrivateTutor ,'s_uni_abbrev': t.university.abbrev, 's_hourly_rate': t.hourly_rate}
        else:
            context = {'msg':msg}

        return render(request, 'edit_profile.html', context)
      
@login_required
def reviewTutor(request, url_token):
    url_not_found = False
    url = ReviewTempUrl.objects.filter(temp_url=url_token).filter(expires__gte=datetime.now())
    if len(url) == 0:
        context={'url_not_found': True}
        return render(request, 'review_tutor.html', context)
    url = url[0]
    if not request.POST:
        student = url.student
        tutor = url.tutor
        context = {'student': student, 'tutor': tutor, 'url_token': url_token}
        return render(request, 'review_tutor.html', context)
    else:
        isAnonymous = False
        if 'isAnonymous' in request.POST and request.POST['isAnonymous']=="True":
            isAnonymous = True
        
        if 'comment' in request.POST and request.POST['comment']!="":
            r = Review(tutor=url.tutor, student = url.student, rating=int(request.POST['rating']), date=getCurrentDatetime() , comment=request.POST['comment'], isAnonymous=isAnonymous)
        else:
            r = Review(tutor=url.tutor, student = url.student, rating=int(request.POST['rating']), date=getCurrentDatetime() ,  isAnonymous=isAnonymous)
        
        r.save()
        url.delete()
        context = {'submitted':True}
        return render(request, 'review_tutor.html', context)

@login_required
def viewWallet(request):
    
    wallet = request.user.profile.wallet

    current = getCurrentDatetime()
    monthBefore = current - timedelta(days=30)
    transactionHistory = Transaction.objects.filter(profile=request.user.profile).filter(date__gte = monthBefore).order_by("-date")

    context={'amount':wallet.amount, 'transactionHistory':transactionHistory}
    return render(request, 'view_wallet.html', context)

@login_required
def viewTimetable(request):
    if request.user.username =="admin":
        return HttpResponse("You logged in as admin.")

    context={}
    msg = ""

    # time table generation
    # 8:30 - 18:30
    d=['','8:30']
    for x in range (9,19):
        d.append("{}:00".format(x))
        d.append("{}:30".format(x))
    row_list=[]
    row_list.append(d)
    current = getCurrentDatetime()
    current = current.replace(hour=8,minute=30,second=0, microsecond=0)
    
    for x in range (0,7):
        current = current.replace(hour=8,minute=30,second=0, microsecond=0)
        temp = [current.date().strftime('%m-%d')]
        temp.append(generateTimetable(current, current+timedelta(minutes=30), request.user.profile))
        for y in range (0,20):
            current = current + timedelta(minutes=30)
            temp.append(generateTimetable(current, current+timedelta(minutes=30), request.user.profile))
        row_list.append(temp)
        current = current.replace(hour=8,minute=30,second=0, microsecond=0)
        current = current + timedelta(days=1)

    context['row_list']=zip(*row_list)

    if request.user.profile.isTutor:
        # second timetable generation
        d=['','8:30']
        for x in range (9,19):
            d.append("{}:00".format(x))
            d.append("{}:30".format(x))
        row_list=[]
        row_list.append(d)
        current = getCurrentDatetime() +timedelta(days=7)
        current = current.replace(hour=8,minute=30,second=0, microsecond=0)
        
        for x in range (0,7):
            current = current.replace(hour=8,minute=30,second=0, microsecond=0)
            temp = [current.date().strftime('%m-%d')]
            temp.append(generateTimetable(current, current+timedelta(minutes=30), request.user.profile))
            for y in range (0,20):
                current = current + timedelta(minutes=30)
                temp.append(generateTimetable(current, current+timedelta(minutes=30), request.user.profile))
            row_list.append(temp)
            current = current.replace(hour=8,minute=30,second=0, microsecond=0)
            current = current + timedelta(days=1)

        context['row_list2']=zip(*row_list)
        # end of second timetable generation
        

    

    if request.POST:
        if request.POST['form_type']=="cancel": # cancel session
            IDs = request.POST.getlist('session_id')
            hasPrivateTutor = False
            hasCancelled = False
            user_debit_amount = 0

            if len(IDs)==0:
                return render(request, 'timetable.html', context)
            
            for each in IDs:
                s = Session.objects.get(pk=each)
                if s.tutor.isPrivateTutor:
                    hasPrivateTutor = True
                    user_debit_amount += bookingRefund(s)
                if s.status =="booked":
                    # send email to tutor
                    sendCancelEmailToTutor(s)
                    msg += "Session at {} from {} to {} canceled successfully.\n".format(s.getBookedDateStr, s.getStartTimeStr, s.getEndTimeStr)
                    hasCancelled = True
                    s.status = "cancelled"
                    s.save()
                else:
                    msg += "Session at {} from {} to {} will begin within 24 hours and cannot be cancelled.\n".format(s.getBookedDateStr, s.getStartTimeStr, s.getEndTimeStr)

            if hasPrivateTutor and hasCancelled:
                        msg += '%.2f'%user_debit_amount + ' HKD has been refunded to your wallet.'
            
            context['msg']=msg
        else:
            if request.user.profile.isTutor:
                start_date = request.POST['blackOutStartDatetime']
                end_date = request.POST['blackOutEndDatetime']
                if start_date!="" and end_date!="":
                    
                    sd = toLocalDatetime(parse_datetime(start_date))
                    ed = toLocalDatetime(parse_datetime(end_date))
                    if sd < ed and getCurrentDatetime() < sd:
                        timeslot = Session(tutor=request.user.profile.tutor, start_date=sd, end_date=ed, isBlackedout=True)
                        timeslot.save()
                        context['msg']="Timeslot you selected has been blacked-out.\n"
                    else:
                        context['msg']="Timeslot you selected is invalid.\n"
    
    

    user_profile = request.user.profile
    context['profile']=user_profile

    current = getCurrentDatetime() 
    nextweek = current + timedelta(days=7)
    next2week = current + timedelta(days=14)

    if user_profile.isStudent :
        s = Session.objects.filter(student=user_profile.student).filter(isBlackedout=False).exclude(status="ended").exclude(status="cancelled").filter(end_date__lte=nextweek).order_by('-booking_date')
        context['student_session_list'] = s
    if user_profile.isTutor:
        s = Session.objects.filter(tutor=user_profile.tutor).filter(isBlackedout=False).exclude(status="ended").exclude(status="cancelled").filter(end_date__lte=next2week).order_by('-booking_date')
        context['tutor_session_list'] = s
        current = getCurrentDatetime()
        b = Session.objects.filter(tutor=user_profile.tutor).filter(isBlackedout=True).filter(end_date__gte=current).filter(end_date__lte=next2week).order_by('-start_date')
        unavailable_time = [ getDatetimeStr(t.start_date)+" to "+getDatetimeStr(t.end_date) for t in b]
        context['blackedOutTimeslots'] = unavailable_time

    

    return render(request, 'timetable.html', context)

@login_required
def bookTutor(request, tutor_id):
    if request.user.username =="admin":
        return HttpResponse("You logged in as admin.")
    
    # get tutor with tutor_id
    tutor = get_object_or_404(Tutor, pk=tutor_id)

    
    context={}

    # get tutor unavaliableTimeslot in next 7 date
    current = getCurrentDatetime()
    week_after = current + timedelta(days=7)
    unavailableTimeObj = Session.objects.filter(tutor=tutor).filter(isBlackedout=True).filter(end_date__gt=current).filter(start_date__lt=week_after)
    occupiedTimeObj = Session.objects.filter(tutor=tutor).exclude(status="cancelled").filter(isBlackedout=False).filter(status="booked").filter(end_date__gt=current).filter(start_date__lt=week_after)
    unavailable_time = [ getDatetimeStr(t.start_date)+" to "+getDatetimeStr(t.end_date) for t in unavailableTimeObj]
    occupied_time = [ getDatetimeStr(t.start_date)+" to "+getDatetimeStr(t.end_date) for t in occupiedTimeObj]
    context['tutor']=tutor
    context['unavailable_time']=unavailable_time
    context['occupied_time']=occupied_time

    if tutor.isPrivateTutor:
        amount = tutor.hourly_rate*Decimal(1.05)
        context['fee']= '%.2f'%amount


    if request.POST:

        # form submitted
        context['msg']=""
        use_coupon = False
        coupon_valid = False
        student = request.user.profile.student
        credited_amount = 0
        booking_date = request.POST['booking_date']
        booking_time = request.POST['booking_time']
        date_start = parse_datetime(booking_date+"T"+booking_time)
        if tutor.isPrivateTutor:
            date_end = date_start+timedelta(hours=1)
        else:
            date_end = date_start+timedelta(minutes=30)
        
        date_start = toLocalDatetime(date_start)
        date_end = toLocalDatetime(date_end)
        # check coupon
        if 'coupon_code' in request.POST and request.POST['coupon_code']!='':
            use_coupon = True
            coupon_code = request.POST['coupon_code']
            if Coupon.validate( str(coupon_code) ):
                coupon_valid = True
        
        # handle coupon invalid error
        if (use_coupon) and (not coupon_valid):
            context['msg']="Coupon Code Invalid."
            return render(request, 'book_tutor.html', context)
        
        # check user wallet amount
        if tutor.isPrivateTutor:
            if not hasSufficientBalance(student, tutor, (use_coupon and coupon_valid) ):
                context['msg']="Insufficient wallet balance."
                return render(request, 'book_tutor.html', context)
        
        booking_time_valid = validateBookingDatetime(date_start, date_end, tutor)
        
        # check booking valid or not
        if not booking_time_valid :
            context['msg']="The timeslot you slected is unavailable. Please select another."
            return render(request, 'book_tutor.html', context)

        fair_book = checkFairBook(date_start, date_end, tutor, student)

        # check booking valid or not
        if not fair_book :
            context['msg']="Student only allowed booking ONE timeslot for the same tutor for any single day."
            return render(request, 'book_tutor.html', context)


        s = Session(student=student,tutor=tutor,booking_date=getCurrentDatetime(), start_date=date_start,end_date=date_end,status="booked", isCouponUsed=(use_coupon and coupon_valid))
        s.save()
        if tutor.isPrivateTutor:
            # credit user wallet
            credited_amount = bookingCredit(s)
        sendBookingEmailToTutor(s)
        sendBookingNotification( s, credited_amount)

        context['msg'] += "You have booked a session with "+tutor.profile.getUserFullName+"\nDate: "+s.getBookedDateStr+"\nTimeslot: "+s.getStartTimeStr+" to "+s.getEndTimeStr
        if tutor.isPrivateTutor:
            context['msg'] += '\n'+('%.2f'%credited_amount) +' has been deducted from your wallet.'
            if use_coupon and coupon_valid:
               context['msg'] += "\nCoupon has been used, 5 percent is saved :)"
        
        # update the occupied time
        occupiedTimeObj = Session.objects.filter(tutor=tutor).filter(isBlackedout=False).filter(status="booked").filter(end_date__gt=current).filter(start_date__lt=week_after)
        occupied_time = [ getDatetimeStr(t.start_date)+" to "+getDatetimeStr(t.end_date) for t in occupiedTimeObj]
        context['occupied_time']=occupied_time

    # time table generation
    # 8:30 - 18:30
    d=['','8:30']
    for x in range (9,19):
        d.append("{}:00".format(x))
        d.append("{}:30".format(x))
    row_list=[]
    row_list.append(d)
    current = getCurrentDatetime() + timedelta(days=1)
    current = current.replace(hour=8,minute=30,second=0, microsecond=0)
    
    for x in range (0,7):
        current = current.replace(hour=8,minute=30,second=0, microsecond=0)
        temp = [current.date().strftime('%m-%d')]
        temp.append(validateBookingDatetime(current, current+timedelta(minutes=30), tutor))
        for y in range (0,20):
            current = current + timedelta(minutes=30)
            temp.append(validateBookingDatetime(current, current+timedelta(minutes=30), tutor))
        row_list.append(temp)
        current = current.replace(hour=8,minute=30,second=0, microsecond=0)
        current = current + timedelta(days=1)

    context['row_list']=zip(*row_list)
    # end of time table generation

    return render(request, 'book_tutor.html', context)

@login_required
def message(request):
    context={'msg':request.session['message'],'title': request.session['title']}
    return render(request, 'message.html', context)

def searchTutor(request):
    
    if not request.GET:
        tag = Tag.objects.all()
        course = Course.objects.all()
        university = University.objects.all()
        context = {'tag': tag, 'course': course, 'university': university }
        return render(request, 'search_tutor.html', context)
    else:
        tutor_list = Tutor.objects.exclude(tutor_type__isnull=True) \
                              .exclude(hourly_rate__isnull=True) \
                              .exclude(university__isnull=True) \
                              .exclude(bio__isnull=True)\
                              .exclude(profile__user__first_name__isnull=True)\
                              .exclude(profile__user__last_name__isnull=True) \
                              .exclude(isHideProfile=True)

        if 'tutor_type' in request.GET:
            t = request.GET['tutor_type']
            tutor_list = tutor_list.filter(tutor_type__tutor_type=t)
        if 'university' in request.GET:
            tutor_list = tutor_list.filter(university__abbrev=request.GET['university'])
        if 'course' in request.GET:
            course_list = request.GET.getlist('course')
            for each in course_list:
                tutor_list = tutor_list.filter(course__code=each)
        if 'tag' in request.GET:
            tag_list = request.GET.getlist('tag')
            for each in tag_list:
                tutor_list = tutor_list.filter(tag__name=each)
        if len(request.GET['first_name'])>0 :
            fn = request.GET['first_name']
            tutor_list = tutor_list.filter(profile__user__first_name=fn)
        if len(request.GET['last_name'])>0:
            ln = request.GET['last_name']
            tutor_list = tutor_list.filter(profile__user__last_name=ln)
        if len(request.GET['min'])>0:
            min = request.GET['min']
            tutor_list = tutor_list.filter(hourly_rate__gte=min)
        if len(request.GET['max'])>0:
            max = request.GET['max']
            tutor_list = tutor_list.filter(hourly_rate__lte=max)
        if 'next7' in request.GET:
            for tutor in tutor_list:
                if not checkNext7day(tutor):
                    tutor_list = tutor_list.exclude(pk=tutor.pk)

        context = {'tag':Tag.objects.all(), 'course': Course.objects.all(),'tutor_list': tutor_list}
        return render(request, 'search_result.html', context)

def viewTutorProfile(request, tutor_id):
    tutor = get_object_or_404(Tutor, pk=tutor_id)
    reviews = Review.objects.filter(tutor=tutor)
    context= {'tutor':tutor, 'reviews': reviews}
    if len(reviews)<3:
        context['noAverage']=True
    return render(request, 'view_tutor_profile.html', context)

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.save()
            user_type = form.cleaned_data['user_type']
            phone_no = form.cleaned_data.get('phone_no')

            createUser(user, user_type, phone_no)

            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=user.username, password=raw_password)
            login(request, user)
            return redirect('homepage')
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})

def notification(request):
    if request.user.username =="admin":
        return HttpResponse("You logged in as admin.")

    if request.POST:
        msg=""
        context={}
        if 'message_id' in request.POST:
            IDs = request.POST.getlist('message_id')

        if len(IDs)==0:
            notif_list = Notification.objects.filter(profile=request.user.profile).order_by('-date')
            context={'list':notif_list,'msg': "No item is selected."}
            return render(request, 'notification.html', context)
        
        for each in IDs:
            try:
                s = Notification.objects.get(pk=each)
            except:
                notif_list = Notification.objects.filter(profile=request.user.profile).order_by('-date')
                context={'list':notif_list,'msg': "Item is already deleted."}
                return render(request, 'notification.html', context)
            s.delete()
        
        msg+="{} notifications has been deleted.".format(len(IDs))
        context['msg']=msg

        notif_list = Notification.objects.filter(profile=request.user.profile).order_by('-date')
        context['list']=notif_list
        return render(request, 'notification.html', context)
    else:
        notif_list = Notification.objects.filter(profile=request.user.profile).order_by('-date')
        context={'list':notif_list}
        return render(request, 'notification.html', context)

def homepage(request):
    return render(request, 'homepage.html')



