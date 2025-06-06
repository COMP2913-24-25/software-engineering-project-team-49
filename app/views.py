from flask import Blueprint

views = Blueprint("views", __name__)

from app import models, db
from flask import render_template, flash, request, redirect, url_for
from flask_login import login_user, current_user, login_required, logout_user
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
from .forms import SignUpForm, LogInForm, AuctionItemForm, BidItemForm, AvailabilityForm, CategoryForm, AssignExpertForm, UnavailableForm, AuthenticateForm, PaymentForm, ConfigFeeForm, AccountUpdateForm, AuthenticationChatForm
from .models import User, Item, ItemStatus, ItemImage, Bid, Notification, AuthenticationRequest, ExpertAvailability, ExpertCategory, UserPriority, AuthenticationMessage, AvailabilityStatus, AuthenticationStatus, Payment, SystemConfiguration, Category
import os, io, base64
import matplotlib.pyplot as plt
from collections import defaultdict
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'app/static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_expert_user(user):
    """
    Safely check if a user is an expert, handling AnonymousUserMixin
    """
    return hasattr(user, 'is_expert') and user.is_expert()

def is_manager_user(user):
    """
    Safely check if a user is a manager, handling AnonymousUserMixin
    """
    return hasattr(user, 'is_manager') and user.is_manager()

@views.route('/')
@views.route('/welcome')
def welcome():
    if is_expert_user(current_user):
        return redirect(url_for('views.expert')) # Redirects to expert home page if user is expert
    if is_manager_user(current_user):
        return redirect(url_for('views.manager')) # Redirects to manager home page if user is manager
    return render_template('welcome.html')

@views.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignUpForm()
    if form.validate_on_submit():
        existing_user = User.query.filter(
            (User.username == form.username.data) | (User.email == form.email.data)
        ).first() # Check if the username or email is already taken
        if existing_user:
            flash("Username or email already in use.", "danger")
            return redirect(url_for('views.signup')) # User will need to input details again

        if form.type.data == '1': # General User
            new_user = User(first_name=form.first_name.data, last_name=form.last_name.data, username=form.username.data, email=form.email.data)
            new_user.set_password(form.password.data)
            db.session.add(new_user)
            db.session.commit()
        elif form.type.data == '2': # Expert
            new_user = User(first_name=form.first_name.data, last_name=form.last_name.data, username=form.username.data, email=form.email.data, priority=UserPriority.EXPERT.value)
            new_user.set_password(form.password.data)
            db.session.add(new_user)
            db.session.commit()
        else: # Manager
            new_user = User(first_name=form.first_name.data, last_name=form.last_name.data, username=form.username.data, email=form.email.data, priority=UserPriority.MANAGER.value)
            new_user.set_password(form.password.data)
            db.session.add(new_user)
            db.session.commit()
        flash('Account successfully created! You will now be redirected to the login page!', 'success')
        return redirect(url_for('views.login')) # Automatically redirect to login page
    return render_template('signup.html', form=form)

@views.route('/login', methods=['GET', 'POST'])
def login():
    form = LogInForm()
    if form.validate_on_submit():
        User = models.User.query.filter_by(username=form.username.data).first() # Find the user by username
        if User and User.check_password(form.password.data): # Checks if the user exists and password matches
            if User.is_manager(): # If user is manager, redirect to manager homepage
                flash('Successfully Logged In!')
                login_user(User)
                return redirect(url_for('views.manager'))
            elif User.is_expert(): # If user is expert, redirect to expert homepage
                flash('Successfully Logged In!')
                login_user(User)
                return redirect(url_for('views.expert'))
            else: # If user is general user, redirect to user homepage
                flash('Successfully Logged In!', 'success')
                login_user(User)
                return redirect(url_for('views.home'))
        else:
            flash("Invalid Username or Password. Please try again.", 'danger') # Invalid login details
    return render_template('login.html', form=form)

@views.route('/logout', methods=['GET','POST'])
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for('views.welcome'))

@views.route('/home')
def home():
    """ Display homepage with 5 auctions that are ending soonest """
    if is_expert_user(current_user):
        return redirect(url_for('views.expert'))
    if is_manager_user(current_user):
        return redirect(url_for('views.manager'))

    now = datetime.utcnow()

    featured_auctions = Item.query.filter(
        Item.status == ItemStatus.ACTIVE.value,
        Item.end_time > now
    ).order_by(Item.end_time.asc()).limit(6).all()

    return render_template('home.html', featured_auctions=featured_auctions)


@views.route('/list_items', methods=['GET', 'POST'])
@login_required
def list_item():
    if is_expert_user(current_user):
        return redirect(url_for('views.expert'))
    if is_manager_user(current_user):
        return redirect(url_for('views.manager'))

    form = AuctionItemForm()

    if form.validate_on_submit():
        auction_end_time = datetime.utcnow() + timedelta(days=int(form.duration.data))

        # Create the auction item
        new_item = Item(
            name=form.name.data,
            description=form.description.data,
            category_id=form.category.data,
            minimum_price=form.minimum_price.data,
            current_price=form.minimum_price.data,
            seller_id=current_user.id,
            start_time=datetime.utcnow(),
            end_time=auction_end_time,
            status=ItemStatus.PENDING.value if form.authentication.data == '1' else ItemStatus.ACTIVE.value
        )

        db.session.add(new_item)
        db.session.commit()

        # Handle Image Uploads
        if 'image' in request.files:
            files = request.files.getlist('image')  # Get list of uploaded images
            for file in files:
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(UPLOAD_FOLDER, filename)
                    file.save(file_path)  # Save image

                    # Create ItemImage entry for the database
                    item_image = ItemImage(item_id=new_item.id, image_path=f'uploads/{filename}')
                    db.session.add(item_image)

        db.session.commit() 

        # Handle authentication request
        if form.authentication.data == '1':
            authentication = AuthenticationRequest(item_id=new_item.id, requester_id=current_user.id)
            db.session.add(authentication)
            db.session.commit()

        flash('Item listed successfully!', 'success')
        return redirect(url_for('views.home'))

    return render_template('list_items.html', form=form)

@views.route('/auction_list')
def auction_list():
    """ Display only active auctions"""
    if is_expert_user(current_user):
        return redirect(url_for('views.expert'))
    if is_manager_user(current_user):
        return redirect(url_for('views.manager'))
    items = Item.query.filter(Item.status == ItemStatus.ACTIVE.value).all()
    return render_template('auction_list.html', items=items)

@views.route('/search', methods=['GET'])
def search():
    """ Search for auction items by name """
    query = request.args.get('query', '').strip()  # Remove leading/trailing spaces
    
    if not query:
        flash("Please enter a search term.", "warning")
        return redirect(url_for('views.auction_list'))  # Redirect if search is empty

    items = Item.query.filter(
        Item.name.ilike(f"%{query}%"), 
        Item.status == ItemStatus.ACTIVE.value  # Only search in active auctions
    ).all()
    
    return render_template('search_results.html', items=items, query=query)

@views.route('/auction_detail/<int:item_id>', methods=['GET', 'POST'])
def auction_detail(item_id):
    """ Display auction details for a single item """
    if is_expert_user(current_user):
        return redirect(url_for('views.expert'))
    if is_manager_user(current_user):
        return redirect(url_for('views.manager'))
    
    item = Item.query.get_or_404(item_id)
    form = BidItemForm(item_price=item.current_price)

    # Fetch the highest bid on item
    highest_bid = Bid.query.filter_by(item_id=item.id).order_by(Bid.amount.desc()).first()

    # Prevent bidding if the auction is not ACTIVE
    if item.status != ItemStatus.ACTIVE.value:
        form = None

    # If user is submitting a bid, confirm they are logged in
    if request.method == 'POST' and item.status == ItemStatus.ACTIVE.value:
        if not current_user.is_authenticated:
            flash("You must be logged in to place a bid.", "warning")
            return redirect(url_for('views.login'))

        if form.validate_on_submit():
            # Prevent self-bidding
            if item.seller_id == current_user.id:
                flash("You cannot bid on your own item.", "danger")
                return redirect(url_for('views.auction_detail', item_id=item.id))

            # Ensure new bid is strictly greater than the last highest
            if highest_bid and form.bid_amount.data <= highest_bid.amount:
                flash(f"Your bid must be greater than £{highest_bid.amount:.2f}.", "danger")
                return redirect(url_for('views.auction_detail', item_id=item.id))
            # Create the new bid
            new_bid = Bid(item_id=item.id, user_id=current_user.id, amount=form.bid_amount.data)
            db.session.add(new_bid)
            item.current_price = form.bid_amount.data
            db.session.commit()

            # Notify the outbid user
            if highest_bid and highest_bid.user_id != current_user.id:
                notification = Notification(
                    user_id=highest_bid.user_id,
                    item_id=item.id,
                    type="outbid",
                    message=f"You have been outbid on '{item.name}'. Current highest bid: £{form.bid_amount.data:.2f}"
                )
                db.session.add(notification)
                db.session.commit()

            flash("Bid placed successfully", "success")
            return redirect(url_for('views.auction_detail', item_id=item.id))

    return render_template('auction_detail.html', item=item, form=form, ItemStatus=ItemStatus)

@views.route('/notifications', methods=['GET'])
@login_required
def notifications():
    if is_expert_user(current_user):
        return redirect(url_for('views.expert'))
    if is_manager_user(current_user):
        return redirect(url_for('views.manager'))
    notifications = Notification.query.filter(Notification.user_id==current_user.id).all()
    return render_template('notifications.html', notifications=notifications)

@views.route('/expert', methods=['GET', 'POST'])
@login_required
def expert():
    if current_user.priority != UserPriority.EXPERT.value: # Ensure only experts can access page
        flash("Access denied.", "danger")
        return redirect(url_for('views.home'))
    from sqlalchemy import or_
    # Query only items pending or second opinion authentication requests assigned to the current expert
    pending_items = Item.query.join(AuthenticationRequest).filter(
        AuthenticationRequest.expert_id == current_user.id,
        or_(
        AuthenticationRequest.status == AuthenticationStatus.PENDING.value,
        AuthenticationRequest.status == AuthenticationStatus.SECOND_OPINION.value
        )
    ).all()
    # Get expert's categories of expertise
    expert_categories = [category.category for category in current_user.expertise]
    return render_template('expert.html', items=pending_items, categories=expert_categories)

@views.route('/select_availability', methods=['GET', 'POST'])
@login_required
def select_availability():
    if current_user.priority != UserPriority.EXPERT.value: # Ensure only experts can access page
        flash("Access denied.", "danger")
        return redirect(url_for('views.home'))
    form = AvailabilityForm() # Initialize availability and unavilability forms
    unavailable = UnavailableForm()
    if 'available_submit' in request.form:  # Handle availablity schedule submission
        ExpertAvailability.query.filter_by(user_id=current_user.id).delete() # Clear existing availability
        availability_data = {
            "Sunday": (form.sunday_start.data, form.sunday_end.data),
            "Monday": (form.monday_start.data, form.monday_end.data),
            "Tuesday": (form.tuesday_start.data, form.tuesday_end.data),
            "Wednesday": (form.wednesday_start.data, form.wednesday_end.data),
            "Thursday": (form.thursday_start.data, form.thursday_end.data),
            "Friday": (form.friday_start.data, form.friday_end.data),
            "Saturday": (form.saturday_start.data, form.saturday_end.data),
        }
        for day, (start, end) in availability_data.items(): # Add new availability
            new_availability = ExpertAvailability(user_id=current_user.id,
                                                         day_of_week=day,
                                                         start_time = datetime.combine(datetime.today(), start),
                                                         end_time = datetime.combine(datetime.today(), end),
                                                         status=AvailabilityStatus.AVAILABLE
                                                        )
            db.session.add(new_availability)
            db.session.commit()
        flash("Availability Added!", "success")
        return redirect(url_for('views.expert')) # Redirect to expert homepage
    elif 'unavailable_submit' in request.form: # Handle unavailablity schedule submission
        ExpertAvailability.query.filter_by(user_id=current_user.id).delete() # Clear existing availability
        availability_data = {
            "Sunday": ("08:00", "20:00"),
            "Monday": ("08:00", "20:00"),
            "Tuesday": ("08:00", "20:00"),
            "Wednesday": ("08:00", "20:00"),
            "Thursday": ("08:00", "20:00"),
            "Friday": ("08:00", "20:00"),
            "Saturday": ("08:00", "20:00"),
        }
        for day, (start, end) in availability_data.items(): # Add new unavailability
            new_availability = ExpertAvailability(user_id=current_user.id,
                                                         day_of_week=day,
                                                         start_time = datetime.combine(datetime.today(), datetime.strptime(start, "%H:%M").time()),
                                                         end_time = datetime.combine(datetime.today(), datetime.strptime(end, "%H:%M").time()),
                                                         status=AvailabilityStatus.UNAVAILABLE
                                                        )
            db.session.add(new_availability)
            db.session.commit()
        flash("Availability Added!", "success")
        return redirect(url_for('views.expert')) # Redirect to expert homepage
    return render_template('select_availability.html', form=form, unavailable=unavailable)

@views.route('/select_category', methods=['GET', 'POST'])
@login_required
def select_category():
    if current_user.priority != UserPriority.EXPERT.value: # Ensure only experts can access page
        flash("Access denied.", "danger")
        return redirect(url_for('views.home'))
    form = CategoryForm()
    if form.validate_on_submit():
        ExpertCategory.query.filter_by(user_id=current_user.id).delete() # Clear existing categories
        for category in form.expert_categories.data: # Add selected categories
            expertise = ExpertCategory(user_id=current_user.id, category=category.name)
            db.session.add(expertise)
        db.session.commit()
        flash('Expertise preferences updated!')
        return redirect(url_for('views.expert')) # Redirect to expert homepage
    return render_template('select_category.html', form=form)

@views.route('/authenticate_item/<int:item_id>', methods=['GET','POST'])
@login_required
def authenticate_item(item_id):
    if current_user.priority != UserPriority.EXPERT.value: # Ensure only experts can access page
        flash("Access denied.", "danger")
        return redirect(url_for('views.home'))
    item = Item.query.get_or_404(item_id)  # Query item by ID
    authentication = AuthenticationRequest.query.filter_by(item_id=item.id).first() # Query authentication request for the item
    action = request.form.get('action') # Get action from form button
    form = AuthenticateForm()
    if form.validate_on_submit():
        if action == 'approve': # If item is approved
            authentication.status = AuthenticationStatus.APPROVED.value
            item.status = ItemStatus.ACTIVE.value
            item.is_authenticated = True
            notification = Notification(user_id=item.seller_id,
                                        item_id=item.id,
                                        type="authentication",
                                        message="Your item has been marked as genuine",
                                        created_at=datetime.utcnow()
                                        )
            db.session.add(notification)
            db.session.commit()
            flash('Item marked as genuine', 'success')
            return redirect(url_for('views.expert')) # Redirect to expert homepage
        elif action == 'reject': # If item is rejected
            authentication.status = AuthenticationStatus.REJECTED.value
            item.status = ItemStatus.ACTIVE.value
            item.is_authenticated = False
            notification = Notification(user_id=item.seller_id,
                                        item_id=item.id,
                                        type="authentication",
                                        message="Your item has been marked as not genuine",
                                        created_at=datetime.utcnow()
                                        )
            db.session.add(notification)
            db.session.commit()
            flash('Item marked as unknown', 'info')
            return redirect(url_for('views.expert')) # Redirect to expert homepage
        elif action == "second_opinion": # If second opinion is requested
            authentication.status = AuthenticationStatus.SECOND_OPINION.value
            notification = Notification(user_id=item.seller_id,
                                        item_id=item.id,
                                        type="authentication",
                                        message="Your item has been requested for a second opinion",
                                        created_at=datetime.utcnow()
                                        )
            db.session.add(notification)
            db.session.commit()
            return redirect(url_for('views.assign_expert', item_id=item_id)) # Redirect to expert homepage
        elif action == "chat": # If expert wants to open dialogue with user
            return redirect(url_for('views.authentication_chat', authentication_id=authentication.id)) # Redirect to expert chat with seller
    return render_template('authenticate_item.html', item=item, form=form)

@views.route('/authentication_chat/<int:authentication_id>', methods=['GET', 'POST'])
@login_required
def authentication_chat(authentication_id):
    authentication = AuthenticationRequest.query.get_or_404(authentication_id) # Get authentication request by ID
    if current_user.id not in [authentication.expert_id, authentication.item.seller_id]: # Ensure only expert/seller can access page
        flash("Access denied.", "danger")
        return redirect(url_for('views.home'))
    messages = AuthenticationMessage.query.filter_by(request_id=authentication_id).order_by(AuthenticationMessage.created_at.asc()).all() # Fetch all messages for this request ordered by creation date
    form = AuthenticationChatForm()
    base_template = "expert_base.html" if current_user.id == authentication.expert_id else "base.html"
    if form.validate_on_submit(): # Create new message for authentication request
        new_message = AuthenticationMessage(request_id=authentication_id,
                                            sender_id=current_user.id,
                                            message=form.message.data,
                                            created_at=datetime.utcnow()
                                            ) # Create notification for user about new message
        notification = Notification(user_id=authentication.requester_id,
                                    item_id=authentication.item_id,
                                    type="authentication",
                                    message="You have received a message from your expert authentication! Please check the chat for more info",
                                    created_at=datetime.utcnow()
                                    )
        db.session.add(new_message)
        db.session.add(notification)
        db.session.commit() # Save to database
        flash("Message Successfully Sent!", "success")
        return redirect(url_for('views.authentication_chat', authentication_id=authentication_id))
    return render_template('authentication_chat.html', form=form, messages=messages, authentication=authentication, base_template=base_template)

@views.route('/manager', methods=['GET', 'POST'])
@login_required
def manager():
    if current_user.priority != UserPriority.MANAGER.value: # Ensure only managers can access page
        flash("Access denied.", "danger")
        return redirect(url_for('views.home'))
    pending_items = Item.query.filter_by(status=ItemStatus.PENDING.value).all() # Fetch all items that are pending
    experts = User.query.filter_by(priority=UserPriority.EXPERT.value).all() # Fetch all experts
    # Create a dictionary mapping expert IDs to their categories then create seperate lists for available and soon to be available experts
    expert_categories = {
        expert.id: [category.category for category in expert.expertise] for expert in experts
    }
    available_experts = User.query.join(ExpertAvailability).filter(User.priority == UserPriority.EXPERT.value).filter(ExpertAvailability.start_time <= datetime.utcnow()).filter(ExpertAvailability.end_time >= datetime.utcnow()).all()
    available_categories = {
        expert.id: [category.category for category in expert.expertise] for expert in available_experts
    }
    upcoming_experts = User.query.join(ExpertAvailability).filter(User.priority == UserPriority.EXPERT.value).filter(ExpertAvailability.start_time > datetime.utcnow()).filter(ExpertAvailability.start_time <= datetime.utcnow() + timedelta(days=7)).all()
    upcoming_categories = {
        expert.id: [category.category for category in expert.expertise] for expert in upcoming_experts
    }
    return render_template('manager.html', items=pending_items, experts=experts, expert_categories=expert_categories, available_experts=available_experts, upcoming_experts=upcoming_experts, available_categories=available_categories, upcoming_categories=upcoming_categories)

@views.route('/assign_expert/<int:item_id>', methods=['GET', 'POST'])
@login_required
def assign_expert(item_id):
    if current_user.priority not in [UserPriority.EXPERT.value, UserPriority.MANAGER.value]: # Ensure only expert/manager can access page
        flash("Access denied.", "danger")
        return redirect(url_for('views.home'))
    item = Item.query.get_or_404(item_id) # Fetch the item by ID
    from sqlalchemy import func
    # Fetch experts who can authenticate the item based on category
    experts = User.query.join(ExpertCategory).filter(
        func.lower(ExpertCategory.category) == func.lower(item.category_rel.name), 
        User.priority == UserPriority.EXPERT.value
    ).all()
    print(f"Eligible experts for category {item.category_id}: {experts}")
    form = AssignExpertForm()
    form.expert.choices = [(expert.id, expert.username) for expert in experts]  # Show experts in form
    if form.validate_on_submit():
        authentication = AuthenticationRequest.query.filter_by(item_id=item.id).first() # Fetch authentication request for item
        authentication.expert_id = form.expert.data # Assign expert to authentication request
        authentication_message = AuthenticationMessage(request_id=authentication.id,
                                                       sender_id=current_user.id,
                                                       message="Please review this item: " + item.name,
                                                       created_at=datetime.utcnow()
                                                       ) # Create a message notifying the expert
        notification = Notification(user_id=form.expert.data, 
                                    item_id=item.id,
                                    type="authentication",
                                    message="Please review this item: " + item.name,
                                    created_at=datetime.utcnow()
                                    ) # Create a notification for the expert
        db.session.add(authentication_message)
        db.session.add(notification)
        db.session.commit() # Save to database
        flash(f"Expert assigned successfully!", "success")
        if current_user.priority == UserPriority.EXPERT.value: # Redirect to expert or manager homepage based on current user's role
            return redirect(url_for('views.expert'))
        else:
            return redirect(url_for('views.manager'))
    return render_template('assign_expert.html', form=form, item=item)

@views.route('/configure_fees', methods=['GET', 'POST'])
def configure_fees():
    if current_user.priority != UserPriority.MANAGER.value: # Ensure only managers can access page
        flash("Access denied.", "danger")
        return redirect(url_for('views.home'))
    form = ConfigFeeForm()
    if form.validate_on_submit(): # Convert fee percentages from form to decimal
        default_fee = form.default_fee.data / 100
        expert_fee = form.expert_fee.data / 100
        for key, value in [('regular_fee_percentage', default_fee), ('authenticated_fee_percentage', expert_fee)]:
            config = SystemConfiguration.query.filter_by(key=key).first() # Update system configuration with the new fee values
            if config:
                config.value = str(value)
            else:
                db.session.add(SystemConfiguration(key=key, value=str(value)))
        db.session.commit()
        flash("Fee percentages updated successfully", "success")
        return redirect(url_for('views.manager'))
    config = SystemConfiguration.query.filter_by(key='regular_fee_percentage').first()
    if config is not None: # Get current fee values from system configuration and populate form
        form.default_fee.data = float(config.value) * 100
    else:
        form.default_fee.data = 1 # If config is empty
    config = SystemConfiguration.query.filter_by(key='authenticated_fee_percentage').first()
    if config is not None:
        form.expert_fee.data = float(config.value) * 100
    else:
        form.expert_fee.data = 5 # If config is empty
    return render_template('configure_fees.html', form=form)

@views.route('/weekly_costs', methods=['GET'])
@login_required
def weekly_costs():
    if current_user.priority != UserPriority.MANAGER.value:
        flash("Access denied.", "danger")
        return redirect(url_for('views.home'))
    
    # Calculate one week ago
    one_week_ago = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=7)
    
    # Fetch all completed payments from past week
    payments = Payment.query.filter(Payment.status=='completed', Payment.completed_at >= one_week_ago).all()
    
    # Generate list of days in past week - full datetime objects
    day_objects = [(one_week_ago + timedelta(days=i)) for i in range(8)]  # Include today
    days = [day.strftime('%Y-%m-%d') for day in day_objects]
    
    # Create dictionaries for daily revenue and fees
    daily_revenue = defaultdict(float)
    daily_fees = defaultdict(float)
    
    # Iterate through the payments and calculate total revenue and fees per day
    for payment in payments:
        
        # Format the date correctly
        string_date = payment.completed_at.strftime('%Y-%m-%d')
        
        daily_revenue[string_date] += payment.amount
        daily_fees[string_date] += payment.fee_amount
    
    
    # Put data in arrays for plotting
    revenues = [daily_revenue[day] for day in days]
    fees = [daily_fees[day] for day in days]
    
    
    # Clear any existing plot
    plt.clf()
    plt.close('all')
    
    # Create the graph for past week's revenue and earnings
    plt.figure(figsize=(10,5))
    plt.plot(days, revenues, marker='o', linestyle='-', linewidth=2, label="Total Revenue (£)")
    plt.plot(days, fees, marker='s', linestyle='-', linewidth=2, label="Total Earnings (£)", color='blue')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.xticks(rotation=45)
    plt.xlabel("Date", fontsize=12)
    plt.ylabel("Amount (£)", fontsize=12)
    plt.title("Revenue and Earnings in the Past Week", fontsize=14)
    plt.legend(loc='best')
    plt.tight_layout()
    
    # Set y-axis to start from 0
    plt.ylim(bottom=0)
    
    # If all values are 0, set a visible y range
    if max(revenues + fees) == 0:
        plt.ylim(top=10)
    
    # Save plot to BytesIO stream with a timestamp to prevent caching
    img = io.BytesIO()
    plt.savefig(img, format='png', dpi=100)
    img.seek(0)
    plot_path = base64.b64encode(img.getvalue()).decode()
    
    # Calculate total revenue, fees and percentage earnings
    total_revenue = sum(payment.amount for payment in payments)
    total_fees = sum(payment.fee_amount for payment in payments)
    percentage_earnings = (total_fees / total_revenue * 100) if total_revenue else 0
    
    return render_template('weekly_costs.html', 
                          payments=payments, 
                          total_revenue=total_revenue, 
                          total_fees=total_fees, 
                          percentage_earnings=percentage_earnings, 
                          plot_path=plot_path)

@views.route('/manage_users', methods=['GET','POST'])
@login_required
def manage_users():
    if current_user.priority != UserPriority.MANAGER.value: # Ensure only managers can access page
        flash("Access denied.", "danger")
        return redirect(url_for('views.home'))
    user_id = request.form.get('user_id') # Retreive form data
    new_role = request.form.get('new_role')
    users = User.query.all() # Get all users
    if request.method == "POST":
        user = User.query.filter_by(id=user_id).first()
        if user: # If user found, update user's role
            user.priority = int(new_role)
            db.session.commit()
            flash("Successfully updated role!", "success")
        else:
            flash("No users found", "danger")
        return redirect(url_for("views.manager")) # Redirect to manager homepage
    return render_template('manage_users.html', users=users, UserPriority=UserPriority)

@views.route('/basket', methods=['GET', 'POST'])
@login_required
def basket():
    if is_expert_user(current_user):
        return redirect(url_for('views.expert'))
    if is_manager_user(current_user):
        return redirect(url_for('views.manager'))
    paying_items = Item.query.filter(Item.status == ItemStatus.PAYING.value, Item.winner_id == current_user.id).all()
    return render_template('basket.html', paying_items = paying_items)

@views.route('/my_watched')
@login_required
def my_watched():
    watched_items = current_user.watched_items.filter(Item.status == ItemStatus.ACTIVE.value).all()
    return render_template('my_watched.html', items=watched_items, active_page='my_watched')


@views.route('/payment_interface/<int:item_id>', methods=['GET', 'POST'])
@login_required
def payment_interface(item_id):
    if is_expert_user(current_user):
        return redirect(url_for('views.expert'))
    if is_manager_user(current_user):
        return redirect(url_for('views.manager'))
    form = PaymentForm()
    item = Item.query.get_or_404(item_id)
    #check if user has saved data
    if current_user.card_number_hash and current_user.card_expiry:
        return redirect(url_for('views.process_payment', item_id=item.id))

    if form.validate_on_submit():
        if form.save_card.data == '1':
            current_user.card_number_hash = generate_password_hash(form.card_number.data)
            current_user.card_expiry = f"{form.expiry_month.data}/{form.expiry_year.data}"
            db.session.commit()
            flash("Card details saved successfully!", "success")
        return redirect(url_for('views.process_payment', item_id=item.id))

    return render_template('payment_interface.html', form=form)

@views.route('/process_payment/<int:item_id>', methods=['GET', 'POST'])
@login_required
def process_payment(item_id):
    item = Item.query.get_or_404(item_id)
    # Ensure the current user is the highest bidder
    highest_bid = Bid.query.filter_by(item_id=item.id).order_by(Bid.amount.desc()).first()
    
    if highest_bid and highest_bid.user_id == current_user.id:
        # Get fee percentage from system configuration
        config = SystemConfiguration.query.filter_by(key='regular_fee_percentage').first()
        if config is not None:
            fee_percentage = float(config.value)
        else:
            fee_percentage = 0.01
        if item.is_authenticated:
            config = SystemConfiguration.query.filter_by(key="authenticated_fee_percentage").first()
            if config is not None:
                fee_percentage = float(config.value)
            else:
                fee_percentage = 0.05
            
        fee_amount = highest_bid.amount * fee_percentage
        
        # Create payment record
        payment = Payment(
            item_id=item.id,
            buyer_id=current_user.id,
            seller_id=item.seller_id,
            amount=highest_bid.amount,
            fee_percentage=fee_percentage,
            fee_amount=fee_amount,
            status='completed',
            completed_at=datetime.utcnow()
        )
        
        db.session.add(payment)
        db.session.commit()
        
        # Send notification to seller
        seller_notification = Notification(
            user_id=item.seller_id,
            item_id=item.id,
            type="payment",
            message=f"Payment completed for '{item.name}'. Amount: £{highest_bid.amount:.2f}"
        )
        #send notification to buyer
        buyer_notification = Notification(
            user_id=item.winner_id,
            item_id=item.id,
            type="payment",
            message=f"Payment completed for '{item.name}'. Amount: £{highest_bid.amount:.2f}"
        )
        item.status = ItemStatus.SOLD.value
        db.session.add(buyer_notification)
        db.session.add(seller_notification)
        db.session.commit()
        
        flash("Payment processed successfully!", "success")
        return redirect(url_for('views.home'))
    else:
        flash("You are not authorized to make this payment.", "danger")
        return redirect(url_for('views.basket'))

@views.route('/watch_item/<int:item_id>', methods=['POST'])
@login_required
def watch_item(item_id):
    item = Item.query.get_or_404(item_id)
    current_user.watched_items.append(item)
    db.session.commit()
    flash(f"Added '{item.name}' to your watchlist!", "success")
    return redirect(url_for('views.auction_detail', item_id=item_id))

@views.route('/unwatch_item/<int:item_id>', methods=['POST'])
@login_required
def unwatch_item(item_id):
    item = Item.query.get_or_404(item_id)
    current_user.watched_items.remove(item)
    db.session.commit()
    flash(f"Removed '{item.name}' from your watchlist.", "info")
    return redirect(url_for('views.auction_detail', item_id=item_id))

@views.route('/watching')
@login_required
def watching():
    if is_expert_user(current_user):
        return redirect(url_for('views.expert'))
    if is_manager_user(current_user):
        return redirect(url_for('views.manager'))
    active_items = [item for item in current_user.watched_items if item.status == ItemStatus.ACTIVE.value]
    return render_template('watching.html', items=active_items)

@views.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    if is_expert_user(current_user):
        return redirect(url_for('views.expert'))
    if is_manager_user(current_user):
        return redirect(url_for('views.manager'))
    form = AccountUpdateForm(current_user)
    
    if form.validate_on_submit():
        # Update user information
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.username = form.username.data
        current_user.email = form.email.data
        
        try:
            db.session.commit()
            flash('Your account has been updated!', 'success')
            return redirect(url_for('views.account'))
        except:
            db.session.rollback()
            flash('An error occurred while updating your account.', 'danger')
    
    # Populate form with current user data on GET request
    elif request.method == 'GET':
        form.first_name.data = current_user.first_name
        form.last_name.data = current_user.last_name
        form.username.data = current_user.username
        form.email.data = current_user.email
    
    return render_template('account.html', form=form)

@views.route('/expert_notifications', methods=['GET'])
@login_required
def expert_notifications():
     if current_user.priority != UserPriority.EXPERT.value:
        flash("Access denied.", "danger")
        return redirect(url_for('views.home'))
     notifications = Notification.query.filter(Notification.user_id==current_user.id).all()
     return render_template('expert_notifications.html', notifications=notifications)

@views.route('/expert_account', methods=['GET', 'POST'])
@login_required
def expert_account():
    if current_user.priority != UserPriority.EXPERT.value:
        flash("Access denied.", "danger")
        return redirect(url_for('views.home'))
    form = AccountUpdateForm(current_user)
    
    if form.validate_on_submit():
        # Update user information
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.username = form.username.data
        current_user.email = form.email.data
        
        try:
            db.session.commit()
            flash('Your account has been updated!', 'success')
            return redirect(url_for('views.expert_account'))
        except:
            db.session.rollback()
            flash('An error occurred while updating your account.', 'danger')
    
    # Populate form with current user data on GET request
    elif request.method == 'GET':
        form.first_name.data = current_user.first_name
        form.last_name.data = current_user.last_name
        form.username.data = current_user.username
        form.email.data = current_user.email
    
    return render_template('expert_account.html', form=form)

@views.route('/manager_account', methods=['GET', 'POST'])
@login_required
def manager_account():
    if current_user.priority != UserPriority.MANAGER.value:
        flash("Access denied.", "danger")
        return redirect(url_for('views.home'))
    form = AccountUpdateForm(current_user)
    
    if form.validate_on_submit():
        # Update user information
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.username = form.username.data
        current_user.email = form.email.data
        
        try:
            db.session.commit()
            flash('Your account has been updated!', 'success')
            return redirect(url_for('views.manager_account'))
        except:
            db.session.rollback()
            flash('An error occurred while updating your account.', 'danger')
    
    # Populate form with current user data on GET request
    elif request.method == 'GET':
        form.first_name.data = current_user.first_name
        form.last_name.data = current_user.last_name
        form.username.data = current_user.username
        form.email.data = current_user.email
    
    return render_template('manager_account.html', form=form)

@views.route('my_auctions', methods=['GET', 'POST'])
@login_required
def my_auctions():
    if is_expert_user(current_user):
        return redirect(url_for('views.expert'))
    if is_manager_user(current_user):
        return redirect(url_for('views.manager'))
    
    my_auctions = current_user.items_sold.all()
    pending_auctions = [item for item in my_auctions if item.status == ItemStatus.PENDING.value]
    for pending_auction in pending_auctions:
        pending_auction.authentication_request = AuthenticationRequest.query.filter_by(item_id=pending_auction.id).first()
    active_auctions = [item for item in my_auctions if item.status == ItemStatus.ACTIVE.value]
    sold_auctions = [item for item in my_auctions if item.status == ItemStatus.SOLD.value]
    expired_auctions = [item for item in my_auctions if item.status == ItemStatus.EXPIRED.value]
    won_auctions = current_user.items_won.filter_by(status=ItemStatus.SOLD.value).all()

    return render_template(
        'my_auctions.html', 
        pending_auctions=pending_auctions,
        active_auctions=active_auctions,
        sold_auctions=sold_auctions,
        expired_auctions=expired_auctions,
        won_auctions=won_auctions
    )

@views.route('/delete_auction/<int:item_id>', methods=['POST'])
@login_required
def delete_auction(item_id):
    item = Item.query.get_or_404(item_id)

    if item.seller_id != current_user.id:
        flash("You don't have permission to delete this auction.", "danger")
        return redirect(url_for('views.my_auctions'))

    # Prevent deletion of sold auctions
    if item.status == ItemStatus.SOLD.value:
        flash("You cannot delete an auction that has already been sold.", "warning")
        return redirect(url_for('views.my_auctions'))
    
    # Delete related authentication messages first
    if item.authentication_request:
        AuthenticationMessage.query.filter_by(request_id=item.authentication_request.id).delete()
        db.session.delete(item.authentication_request)

    db.session.delete(item)
    db.session.commit()
    
    flash("Auction deleted successfully.", "success")
    return redirect(url_for('views.my_auctions'))

@views.route('/manage_categories', methods=['GET', 'POST'])
@login_required
def manage_categories():
    if current_user.priority != UserPriority.MANAGER.value:
        flash("Access denied.", "danger")
        return redirect(url_for('views.home'))

    categories = Category.query.all()

    if request.method == 'POST':
        category_name = request.form.get('category_name').strip()

        if not category_name:
            flash("Category name cannot be empty.", "danger")
        elif Category.query.filter_by(name=category_name).first():
            flash("Category name already exists. Please choose a different name.", "danger")
        else:
            new_category = Category(name=category_name)
            db.session.add(new_category)
            db.session.commit()
            flash("Category added successfully!", "success")

        return redirect(url_for('views.manage_categories'))

    return render_template('manage_categories.html', categories=categories)



@views.route('/delete_category/<int:category_id>', methods=['POST'])
@login_required
def delete_category(category_id):
    if current_user.priority != UserPriority.MANAGER.value:
        flash("Access denied.", "danger")
        return redirect(url_for('views.home'))

    category = Category.query.get_or_404(category_id)

    if category.items.count() > 0:
        flash("Cannot delete category while items are still assigned to it. Please reassign or remove the items first.", "danger")
        return redirect(url_for('views.manage_categories'))
    
    db.session.delete(category)
    db.session.commit()
    flash("Category deleted successfully!", "success")

    return redirect(url_for('views.manage_categories'))