from django.http import HttpResponse
from django.template import RequestContext
from django.shortcuts import render_to_response
from rango.models import Category, Page
from rango.forms import CategoryForm, PageForm
from rango.forms import UserForm, UserProfileForm


def encode_url(str):
    return str.replace(' ', '_')

def decode_url(str):
    return str.replace('_', ' ')

# DON'T UNDERSTAND HOW IT WORKS
def get_category_list(max_results=0, starts_with=''):
    cat_list = []
    if starts_with:
        cat_list = Category.objects.filter(name__startswith=starts_with)
    else:
        cat_list = Category.objects.all()

    if max_results > 0:
        if (len(cat_list) > max_results):
            cat_list = cat_list[:max_results]

    for cat in cat_list:
        cat.url = encode_url(cat.name)
    
    return cat_list

def index(request):
    # Obtain the context from the HTTP request.
    context = RequestContext(request)

    # Query the database for a list of ALL categories currently stored.
    # Order the categories by no. likes in descending order.
    # Retrieve the top 5 only - or all if less than 5.
    # Place the list in our context_dict dictionary which will be passed to the template engine.
    category_list = Category.objects.order_by('-likes')[:10]
    page_list = Page.objects.order_by('-views')[:10]    
    context_dict = {'categories': category_list, 'pages': page_list}

    # The following two lines are new.
    # We loop through each category returned, and create a URL attribute.
    # This attribute stores an encoded URL (e.g. spaces replaced with underscores).
    for category in category_list:
        category.url = category.name.replace(' ', '_')

    cat_list = get_category_list() # DON'T UNDERSTAND
    context_dict['cat_list'] = cat_list # DON'T UNDERSTAND              

    # Render the response and send it back!
    return render_to_response('rango/index.html', context_dict, context)
def add_category(request):
    # Get the context from the request.
    context = RequestContext(request)

    # A HTTP POST?
    if request.method == 'POST':
        form = CategoryForm(request.POST)

        # Have we been provided with a valid form?
        if form.is_valid():
            # Save the new category to the database.
            form.save(commit=True)

            # Now call the index() view.
            # The user will be shown the homepage.
            return index(request)
        else:
            # The supplied form contained errors - just print them to the terminal.
            print form.errors
    else:
        # If the request was not a POST, display the form to enter details.
        form = CategoryForm()

    cat_list = get_category_list() # DON'T UNDERSTAND
    # context_dict['cat_list'] = cat_list # DON'T UNDERSTAND        

    # Bad form (or form details), no form supplied...
    # Render the form with error messages (if any).
    return render_to_response('rango/add_category.html', {'form': form, 'cat_list': cat_list}, context)        


def category(request, category_name_url):
    context = RequestContext(request)
    result_list = []

    if request.method == 'POST':
        query = request.POST['query'].strip()

        if query:
            # Run our Bing function to get the results list!
            result_list = run_query(query)

    # Change underscores in the category name to spaces.
    # URLs don't handle spaces well, so we encode them as underscores.
    # We can then simply replace the underscores with spaces again to get the name.
    category_name = category_name_url.replace('_', ' ')

    # Create a context dictionary which we can pass to the template rendering engine.
    # We start by containing the name of the category passed by the user.
    context_dict = {'category_name': category_name, 'category_name_url': category_name_url}

    cat_list = get_category_list() # DON'T UNDERSTAND
    context_dict['cat_list'] = cat_list # DON'T UNDERSTAND 
    context_dict['result_list'] = result_list        
    try:
        # Can we find a category with the given name?
        # If we can't, the .get() method raises a DoesNotExist exception.
        # So the .get() method returns one model instance or raises an exception.
        # category = Category.objects.get(name=category_name)
        category = Category.objects.get(name__iexact=category_name) # DON'T UNDERSTAND
        context_dict['category'] = category

        # Retrieve all of the associated pages.
        # Note that filter returns >= 1 model instance.
        # pages = Page.objects.filter(category=category)
        pages = Page.objects.filter(category=category).order_by('-views') # DON'T UNDERSTAND
        
        # Adds our results list to the template context under name pages.
        context_dict['pages'] = pages
        # We also add the category object from the database to the context dictionary.
        # We'll use this in the template to verify that the category exists.
        # context_dict['category'] = category

    except Category.DoesNotExist:
        # We get here if we didn't find the specified category.
        # Don't do anything - the template displays the "no category" message for us.
        pass  
                           
    return render_to_response('rango/category.html', context_dict, context)


def about(request):
    # Request the context of the request.
    # The context contains information such as the client's machine details, for example.
    context = RequestContext(request)

    # Construct a dictionary to pass to the template engine as its context.
    # Note the key boldmessage is the same as {{ boldmessage }} in the template!
    context_dict = {'nextStep': "I can fix all django projects, and make everything work"}

    cat_list = get_category_list() # DON'T UNDERSTAND
    context_dict['cat_list'] = cat_list # DON'T UNDERSTAND    

    # Return a rendered response to send to the client.
    # We make use of the shortcut function to make our lives easier.
    # Note that the first parameter is the template we wish to use.
    return render_to_response('rango/about.html', context_dict, context)


def register(request):
    # Like before, get the request's context.
    context = RequestContext(request)

    # A boolean value for telling the template whether the registration was successful.
    # Set to False initially. Code changes value to True when registration succeeds.
    registered = False

    # If it's a HTTP POST, we're interested in processing form data.
    if request.method == 'POST':
        # Attempt to grab information from the raw form information.
        # Note that we make use of both UserForm and UserProfileForm.
        user_form = UserForm(data=request.POST)
        profile_form = UserProfileForm(data=request.POST)

        # If the two forms are valid...
        if user_form.is_valid() and profile_form.is_valid():
            # Save the user's form data to the database.
            user = user_form.save()

            # Now we hash the password with the set_password method.
            # Once hashed, we can update the user object.
            user.set_password(user.password)
            user.save()

            # Now sort out the UserProfile instance.
            # Since we need to set the user attribute ourselves, we set commit=False.
            # This delays saving the model until we're ready to avoid integrity problems.
            profile = profile_form.save(commit=False)
            profile.user = user

            # Did the user provide a profile picture?
            # If so, we need to get it from the input form and put it in the UserProfile model.
            if 'picture' in request.FILES:
                profile.picture = request.FILES['picture']

            # Now we save the UserProfile model instance.
            profile.save()

            # Update our variable to tell the template registration was successful.
            registered = True

        # Invalid form or forms - mistakes or something else?
        # Print problems to the terminal.
        # They'll also be shown to the user.
        else:
            print user_form.errors, profile_form.errors

    # Not a HTTP POST, so we render our form using two ModelForm instances.
    # These forms will be blank, ready for user input.
    else:
        user_form = UserForm()
        profile_form = UserProfileForm()

    # Render the template depending on the context.
    return render_to_response(
            'rango/register.html',
            {'user_form': user_form, 'profile_form': profile_form, 'registered': registered},
            context)
def user_login(request):
    # Like before, obtain the context for the user's request.
    context = RequestContext(request)

    # If the request is a HTTP POST, try to pull out the relevant information.
    if request.method == 'POST':
        # Gather the username and password provided by the user.
        # This information is obtained from the login form.
        username = request.POST['username']
        password = request.POST['password']

        # Use Django's machinery to attempt to see if the username/password
        # combination is valid - a User object is returned if it is.
        user = authenticate(username=username, password=password)

        # If we have a User object, the details are correct.
        # If None (Python's way of representing the absence of a value), no user
        # with matching credentials was found.
        if user:
            # Is the account active? It could have been disabled.
            if user.is_active:
                # If the account is valid and active, we can log the user in.
                # We'll send the user back to the homepage.
                login(request, user)
                return HttpResponseRedirect('/rango/')
            else:
                # An inactive account was used - no logging in!
                return HttpResponse("Your Rango account is disabled.")
        else:
            # Bad login details were provided. So we can't log the user in.
            print "Invalid login details: {0}, {1}".format(username, password)
            return HttpResponse("Invalid login details supplied.")

    # The request is not a HTTP POST, so display the login form.
    # This scenario would most likely be a HTTP GET.
    else:
        # No context variables to pass to the template system, hence the
        # blank dictionary object...
        return render_to_response('rango/login.html', {}, context)   
def restricted(request):
    # Request the context of the request.
    # The context contains information such as the client's machine details, for example.
    context = RequestContext(request)

    # Construct a dictionary to pass to the template engine as its context.
    # Note the key boldmessage is the same as {{ boldmessage }} in the template!
    context_dict = {'nextStep': "I can fix all django projects, and make everything work"}

    cat_list = get_category_list() # DON'T UNDERSTAND
    context_dict['cat_list'] = cat_list # DON'T UNDERSTAND    

    # Return a rendered response to send to the client.
    # We make use of the shortcut function to make our lives easier.
    # Note that the first parameter is the template we wish to use.
    return render_to_response('rango/restricted.html', context_dict, context)

def track_url(request):
    context = RequestContext(request)
    page_id = None
    url = '/rango/'
    if request.method == 'GET':
        if 'page_id' in request.GET:
            page_id = request.GET['page_id']
            try:
                page = Page.objects.get(id=page_id)
                page.views = page.views + 1
                page.save()
                url = page.url
            except:
                pass
        
    return redirect(url)

    # # per github
# def add_page(request, category_name_url):
#     context = RequestContext(request)
#     cat_list = get_category_list()
#     context_dict = {}
#     context_dict['cat_list'] = cat_list

#     category_name = decode_url(category_name_url)
#     if request.method == 'POST':
#         form = PageForm(request.POST)
        
#         if form.is_valid():
#             # This time we cannot commit straight away.
#             # Not all fields are automatically populated!
#             page = form.save(commit=False)

#             # Retrieve the associated Category object so we can add it.
#             try:
#                 cat = Category.objects.get(name=category_name)
#                 page.category = cat
#             except Category.DoesNotExist:
#                 return render_to_response( 'rango/add_page.html',
#                                           context_dict,
#                                           context)

#             # Also, create a default value for the number of views.
#             page.views = 0

#             # With this, we can then save our new model instance.
#             page.save()

#             # Now that the page is saved, display the category instead.
#             return category(request, category_name_url)
#         else:
#             print form.errors
#     else:
#         form = PageForm()

#     context_dict['category_name_url']= category_name_url
#     context_dict['category_name'] =  category_name
#     context_dict['form'] = form

#     return render_to_response( 'rango/add_page.html',
#                                context_dict,
#                                context)


def logout(request):
    # As we can assume the user is logged in, we can just log them out.
    logout(request)

    # Take the user back to the homepage.
    return HttpResponseRedirect('/rango/')            

def search(request):
    context = RequestContext(request)
    result_list = []

    if request.method == 'POST':
        query = request.POST['query'].strip()

        if query:
            # Run our Bing function to get the results list!
            result_list = run_query(query)

    cat_list = get_category_list() # DON'T UNDERSTAND
    # context_dict['cat_list'] = cat_list # DON'T UNDERSTAND             

    return render_to_response('rango/search.html', {'result_list': result_list, 'cat_list': cat_list}, context)

# login_required

def profile(request):
    context = RequestContext(request)

    cat_list = get_category_list() # DON'T UNDERSTAND
    context_dict = {'cat_list': cat_list}
    u = User.objects.get(username=request.user)

    try:      
        up = UserProfile.objects.get(user=u)
    except:
        up = None

    context_dict['user'] = u
    context_dict['userprofile'] = up

    return render_to_response('rango/profile.html', context_dict, context)
