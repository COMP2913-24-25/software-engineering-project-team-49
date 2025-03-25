from flask import Blueprint

views = Blueprint("views", __name__)

from app import models, db
from flask import render_template, flash, request, redirect, url_for
from flask_login import login_user, current_user, login_required, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from .forms import SignUpForm, LogInForm, AuctionItemForm, BidItemForm, AvailabilityForm, CategoryForm, AssignExpertForm, UnavailableForm, AuthenticateForm, PaymentForm
from .models import User, Item, ItemStatus,ItemImage, Category, Bid, Notification, AuthenticationRequest, ExpertAvailability, ExpertCategory, UserPriority, AuthenticationMessage, AvailabilityStatus, AuthenticationStatus, Payment
import os
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'app/static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@views.route('/')
@views.route('/welcome')
def welcome():
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

        new_user = User(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            username=form.username.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data),
            priority=1
        )
        db.session.add(new_user)
        db.session.commit()
        flash("Account successfully created", "success")
        return redirect(url_for('views.login'))
    return render_template('signup.html', form=form, signup='signup')

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
    now = datetime.utcnow()

    featured_auctions = Item.query.filter(
        Item.status == ItemStatus.ACTIVE.value,
        Item.end_time > now
    ).order_by(Item.end_time.asc()).limit(5).all()

    return render_template('home.html', featured_auctions=featured_auctions)


@views.route('/list_items', methods=['GET', 'POST'])
@login_required
def list_item():
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
     notifications = Notification.query.filter(Notification.user_id==current_user.id)
     return render_template('notifications.html', notifications=notifications)

@views.route('/expert', methods=['GET', 'POST'])
@login_required
def expert():
    if current_user.priority != UserPriority.EXPERT.value:
        flash("Access denied.", "danger")
        return redirect(url_for('views.home'))

    pending_items = AuthenticationRequest.query.join(Item).filter(
        AuthenticationRequest.expert_id == current_user.id,
        AuthenticationRequest.status == AuthenticationStatus.PENDING.value
    ).all()
    return render_template('expert.html', items=pending_items)

@views.route('/select_availability', methods=['GET', 'POST'])
@login_required
def select_availability():
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
    pending_items = Item.query.filter_by(status=ItemStatus.PENDING.value).all()
    experts = User.query.filter_by(priority=UserPriority.EXPERT.value).all()
    return render_template('manager.html', items=pending_items, experts=experts)

@views.route('/assign_expert/<int:item_id>', methods=['GET', 'POST'])
@login_required
def assign_expert(item_id):
    item = Item.query.get_or_404(item_id)
    experts = User.query.join(ExpertCategory).filter(ExpertCategory.category == item.category_rel.name, User.priority == UserPriority.EXPERT.value).all()
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

@views.route('/basket', methods=['GET', 'POST'])
@login_required
def basket():
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
        fee_percentage = 0.01  # Default 1%
        if item.is_authenticated:
            fee_percentage = 0.05  # 5% for authenticated items
            
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

@views.route('/toggle_watch/<int:item_id>', methods=['POST'])
@login_required
def toggle_watch(item_id):
    item = Item.query.get_or_404(item_id)

    if current_user in item.watchers:
        item.watchers.remove(current_user)
        flash(f"Removed '{item.name}' from your watchlist.", "info")
    else:
        item.watchers.append(current_user)
        flash(f"Added '{item.name}' to your watchlist!", "success")

    db.session.commit()
    return redirect(request.form.get("next") or url_for('views.auction_detail', item_id=item_id))
