from flask import Blueprint

views = Blueprint("views", __name__)

from app import models, db
from flask import render_template, flash, request, redirect, url_for
from flask_login import login_user, current_user, login_required, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from .forms import SignUpForm, LogInForm, AuctionItemForm, BidItemForm, AvailabilityForm, CategoryForm, AssignExpertForm, UnavailableForm, AuthenticateForm, PaymentForm, ConfigFeeForm, AccountUpdateForm
from .models import User, Item, ItemStatus,ItemImage, Category, Bid, Notification, AuthenticationRequest, ExpertAvailability, ExpertCategory, UserPriority, AuthenticationMessage, AvailabilityStatus, AuthenticationStatus, Payment, SystemConfiguration
import os
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
        return redirect(url_for('views.expert'))
    if is_manager_user(current_user):
        return redirect(url_for('views.manager'))
    return render_template('welcome.html')

@views.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignUpForm()
    if form.validate_on_submit():
        existing_user = User.query.filter(
            (User.username == form.username.data) | (User.email == form.email.data)
        ).first()
        if existing_user:
            flash("Username or email already in use.", "danger")
            return redirect(url_for('views.signup'))

        if form.type.data == '1':
            new_user = User(first_name=form.first_name.data, last_name=form.last_name.data, username=form.username.data, email=form.email.data)
            new_user.set_password(form.password.data)
            db.session.add(new_user)
            db.session.commit()
        elif form.type.data == '2':
            new_user = User(first_name=form.first_name.data, last_name=form.last_name.data, username=form.username.data, email=form.email.data, priority=UserPriority.EXPERT.value)
            new_user.set_password(form.password.data)
            db.session.add(new_user)
            db.session.commit()
        else:
            new_user = User(first_name=form.first_name.data, last_name=form.last_name.data, username=form.username.data, email=form.email.data, priority=UserPriority.MANAGER.value)
            new_user.set_password(form.password.data)
            db.session.add(new_user)
            db.session.commit()
        flash('Account successfully created! You will now be redirected to the login page!', 'success')
        return redirect(url_for('views.login'))
    return render_template('signup.html', form=form)

@views.route('/login', methods=['GET', 'POST'])
def login():
    form = LogInForm()
    if form.validate_on_submit():
        User = models.User.query.filter_by(username=form.username.data).first()
        if User and User.check_password(form.password.data):
            if User.is_manager():
                flash('Successfully Logged In!')
                login_user(User)
                return redirect(url_for('views.manager'))
            elif User.is_expert():
                flash('Successfully Logged In!')
                login_user(User)
                return redirect(url_for('views.expert'))
            else:
                flash('Successfully Logged In!', 'success')
                login_user(User)
                return redirect(url_for('views.home'))
        else:
            flash("Invalid Username or Password. Please try again.", 'danger')
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

    # If user is submitting a bid, confirm they are logged in
    if request.method == 'POST':
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

    return render_template('auction_detail.html', item=item, form=form)

@views.route('/notifications', methods=['GET'])
@login_required
def notifications():
    if is_expert_user(current_user):
        return redirect(url_for('views.expert'))
    if is_manager_user(current_user):
        return redirect(url_for('views.manager'))
    notifications = Notification.query.filter(Notification.user_id==current_user.id)
    return render_template('notifications.html', notifications=notifications)

@views.route('/expert', methods=['GET', 'POST'])
@login_required
def expert():
    if current_user.priority != UserPriority.EXPERT.value:
        flash("Access denied.", "danger")
        return redirect(url_for('views.home'))

    pending_items = Item.query.join(AuthenticationRequest).filter(
        AuthenticationRequest.expert_id == current_user.id,
        AuthenticationRequest.status == AuthenticationStatus.PENDING.value
    ).all()

    expert_categories = [category.category for category in current_user.expertise]
    return render_template('expert.html', items=pending_items, categories=expert_categories)

@views.route('/select_availability', methods=['GET', 'POST'])
@login_required
def select_availability():
    if current_user.priority != UserPriority.EXPERT.value:
        flash("Access denied.", "danger")
        return redirect(url_for('views.home'))
    form = AvailabilityForm()
    unavailable = UnavailableForm()
    if 'available_submit' in request.form:
        ExpertAvailability.query.filter_by(user_id=current_user.id).delete()
        availability_data = {
            "Sunday": (form.sunday_start.data, form.sunday_end.data),
            "Monday": (form.monday_start.data, form.monday_end.data),
            "Tuesday": (form.tuesday_start.data, form.tuesday_end.data),
            "Wednesday": (form.wednesday_start.data, form.wednesday_end.data),
            "Thursday": (form.thursday_start.data, form.thursday_end.data),
            "Friday": (form.friday_start.data, form.friday_end.data),
            "Saturday": (form.saturday_start.data, form.saturday_end.data),
        }
        for day, (start, end) in availability_data.items():
            new_availability = ExpertAvailability(user_id=current_user.id,
                                                         day_of_week=day,
                                                         start_time = datetime.combine(datetime.today(), start),
                                                         end_time = datetime.combine(datetime.today(), end),
                                                         status=AvailabilityStatus.AVAILABLE
                                                        )
            db.session.add(new_availability)
            db.session.commit()
        flash("Availability Added!", "success")
        return redirect(url_for('views.expert'))
    elif 'unavailable_submit' in request.form:
        ExpertAvailability.query.filter_by(user_id=current_user.id).delete()
        availability_data = {
            "Sunday": ("08:00", "20:00"),
            "Monday": ("08:00", "20:00"),
            "Tuesday": ("08:00", "20:00"),
            "Wednesday": ("08:00", "20:00"),
            "Thursday": ("08:00", "20:00"),
            "Friday": ("08:00", "20:00"),
            "Saturday": ("08:00", "20:00"),
        }
        for day, (start, end) in availability_data.items():
            new_availability = ExpertAvailability(user_id=current_user.id,
                                                         day_of_week=day,
                                                         start_time = datetime.combine(datetime.today(), datetime.strptime(start, "%H:%M").time()),
                                                         end_time = datetime.combine(datetime.today(), datetime.strptime(end, "%H:%M").time()),
                                                         status=AvailabilityStatus.UNAVAILABLE
                                                        )
            db.session.add(new_availability)
            db.session.commit()
        flash("Availability Added!", "success")
        return redirect(url_for('views.expert'))
    return render_template('select_availability.html', form=form, unavailable=unavailable)

@views.route('/select_category', methods=['GET', 'POST'])
@login_required
def select_category():
    if current_user.priority != UserPriority.EXPERT.value:
        flash("Access denied.", "danger")
        return redirect(url_for('views.home'))
    form = CategoryForm()
    if form.validate_on_submit():
        ExpertCategory.query.filter_by(user_id=current_user.id).delete()
        for category in form.expert_categories.data:
            expertise = ExpertCategory(user_id=current_user.id, category=category.name)
            db.session.add(expertise)
        db.session.commit()
        flash('Expertise preferences updated!')
        return redirect(url_for('views.expert'))
    return render_template('select_category.html', form=form)

@views.route('/authenticate_item/<int:item_id>', methods=['GET','POST'])
@login_required
def authenticate_item(item_id):
    if current_user.priority != UserPriority.EXPERT.value:
        flash("Access denied.", "danger")
        return redirect(url_for('views.home'))
    item = Item.query.get_or_404(item_id)
    authentication = AuthenticationRequest.query.filter_by(item_id=item.id).first()
    action = request.form.get('action')
    form = AuthenticateForm()
    if form.validate_on_submit():
        if action == 'approve':
            authentication.status = AuthenticationStatus.APPROVED.value
            item.status = ItemStatus.ACTIVE.value
            item.is_authenticated = True
            db.session.commit()
            flash('Item marked as genuine', 'success')
            return redirect(url_for('views.expert'))
        elif action == 'reject':
            authentication.status = AuthenticationStatus.REJECTED.value
            item.status = ItemStatus.ACTIVE.value
            item.is_authenticated = False
            db.session.commit()
            flash('Item marked as unknown', 'info')
            return redirect(url_for('views.expert'))
    return render_template('authenticate_item.html', item=item, form=form)

@views.route('/manager', methods=['GET', 'POST'])
@login_required
def manager():
    if current_user.priority != UserPriority.MANAGER.value:
        flash("Access denied.", "danger")
        return redirect(url_for('views.home'))
    pending_items = Item.query.filter_by(status=ItemStatus.PENDING.value).all()
    experts = User.query.filter_by(priority=UserPriority.EXPERT.value).all()
    # Create a dictionary mapping expert IDs to their categories
    expert_categories = {
        expert.id: [category.category for category in expert.expertise] for expert in experts
    }
    return render_template('manager.html', items=pending_items, experts=experts, expert_categories=expert_categories)

@views.route('/assign_expert/<int:item_id>', methods=['GET', 'POST'])
@login_required
def assign_expert(item_id):
    if current_user.priority != UserPriority.MANAGER.value:
        flash("Access denied.", "danger")
        return redirect(url_for('views.home'))
    item = Item.query.get_or_404(item_id)
    from sqlalchemy import func

    experts = User.query.join(ExpertCategory).filter(
        func.lower(ExpertCategory.category) == func.lower(item.category_rel.name), 
        User.priority == UserPriority.EXPERT.value
    ).all()
    print(f"Eligible experts for category {item.category_id}: {experts}")
    form = AssignExpertForm()
    form.expert.choices = [(expert.id, expert.username) for expert in experts]
    if form.validate_on_submit():
        authentication = AuthenticationRequest.query.filter_by(item_id=item.id).first()
        authentication.expert_id = form.expert.data
        authentication_message = AuthenticationMessage(request_id=authentication.id,
                                                       sender_id=current_user.id,
                                                       message="Please review this item: " + item.name,
                                                       created_at=datetime.utcnow()
                                                       )
        notification = Notification(user_id=form.expert.data, 
                                    item_id=item.id,
                                    type="authentication",
                                    message="Please review this item: " + item.name,
                                    created_at=datetime.utcnow()
                                    )
        db.session.add(authentication_message)
        db.session.add(notification)
        db.session.commit()
        flash(f"Expert assigned successfully!", "success")
        return redirect(url_for('views.manager'))
    return render_template('assign_expert.html', form=form, item=item)

@views.route('/configure_fees', methods=['GET', 'POST'])
def configure_fees():
    if current_user.priority != UserPriority.MANAGER.value:
        flash("Access denied.", "danger")
        return redirect(url_for('views.home'))
    form = ConfigFeeForm()
    if form.validate_on_submit():
        default_fee = form.default_fee.data / 100
        expert_fee = form.expert_fee.data / 100
        for key, value in [('regular_fee_percentage', default_fee), ('authenticated_fee_percentage', expert_fee)]:
            config = SystemConfiguration.query.filter_by(key=key).first()
            if config:
                config.value = str(value)
            else:
                db.session.add(SystemConfiguration(key=key, value=str(value)))
        db.session.commit()
        flash("Fee percentages updated successfully", "success")
        return redirect(url_for('views.manager'))
    config = SystemConfiguration.query.filter_by(key='regular_fee_percentage').first()
    if config is not None:
        form.default_fee.data = float(config.value) * 100
    else:
        form.default_fee.data = 1
    config = SystemConfiguration.query.filter_by(key='authenticated_fee_percentage').first()
    if config is not None:
        form.expert_fee.data = float(config.value) * 100
    else:
        form.expert_fee.data = 5
    return render_template('configure_fees.html', form=form)

@views.route('/weekly_costs', methods=['GET'])
@login_required
def weekly_costs():
    if current_user.priority != UserPriority.MANAGER.value:
        flash("Access denied.", "danger")
        return redirect(url_for('views.home'))
    one_week_ago = datetime.utcnow() - timedelta(days=7)
    payments = Payment.query.filter(Payment.status=='completed', Payment.completed_at >= one_week_ago).all()
    total_revenue = sum(payment.amount for payment in payments)
    total_fees = sum(payment.fee_amount for payment in payments)
    percentage_earnings = (total_fees / total_revenue * 100) if total_revenue else 0
    return render_template('weekly_costs.html', payments=payments, total_revenue=total_revenue, total_fees=total_fees, percentage_earnings=percentage_earnings)

@views.route('/manage_users', methods=['GET','POST'])
@login_required
def manage_users():
    if current_user.priority != UserPriority.MANAGER.value:
        flash("Access denied.", "danger")
        return redirect(url_for('views.home'))
    user_id = request.form.get('user_id')
    new_role = request.form.get('new_role')
    users = User.query.all()
    if request.method == "POST":
        user = User.query.filter_by(id=user_id).first()
        if user:
            user.priority = int(new_role)
            db.session.commit()
            flash("Successfully updated role!", "success")
        else:
            flash("No users found", "danger")
        return redirect(url_for("views.manager"))
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
    items = current_user.watched_items.all()
    return render_template('watching.html', items=items)

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
     notifications = Notification.query.filter(Notification.user_id==current_user.id)
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