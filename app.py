import logging
from flask import Flask, render_template, redirect, url_for, request, jsonify
import random
import time
import csv
from flask import send_file
import io
import locale
from babel.numbers import format_currency, format_number
#from decimal import Decimal, ROUND_DOWN

app = Flask(__name__)
locale.setlocale(locale.LC_ALL, 'pl_PL.UTF-8')

# Set up logging
logger = logging.getLogger()
#log = logging.getLogger('werkzeug')
#log.setLevel(logging.Error)  # Ustawienie logowania na ERROR, żeby wyciszyć INFO i DEBUG

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)  # Log everything from DEBUG level and above
console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)

# File handler
file_handler = logging.FileHandler('auction_system.log')
file_handler.setLevel(logging.DEBUG)  # Log everything from DEBUG level and above
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)

# Add both handlers to the logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# Lista użytkowników
users = ['telekom1', 'telekom2', 'telekom3', 'telekom4']
start_price_value = locale.format_string('%.0f', 356000, grouping=True)
logged_in_users = {}

start_price_value = 356000 
start_price_bid_increment = 7120



auction_data = {
    'round_time': 2222,
    'break_time': 15,
    'start_price': 356000,
    'bid_increment': 7120,
    'current_round': 0,
    'status': 'waiting',
    'bids': [],
    'results': [],
    'current_leaders': {block: None for block in ['A', 'B', 'C', 'D', 'E', 'F', 'G']},
    'block_data': {
        'A': {
            'start_price': start_price_value, 
            'bid_increment': round(start_price_value * 0.02),  # 2% of start price
            'bid_amount': round(start_price_value * 1.02)  # Start price * 1.02
        },
        'B': {
            'start_price': 356000, 
            'bid_increment': round(356000 * 0.02), 
            'bid_amount': round(356000 * 1.02)
        },
        'C': {
            'start_price': 356000, 
            'bid_increment': round(356000 * 0.02), 
            'bid_amount': round(356000 * 1.02)
        },
        'D': {
            'start_price': 356000, 
            'bid_increment': round(356000 * 0.02), 
            'bid_amount': round(356000 * 1.02)
        },
        'E': {
            'start_price': 356000, 
            'bid_increment': round(356000 * 0.02), 
            'bid_amount': round(356000 * 1.02)
        },
        'F': {
            'start_price': 356000, 
            'bid_increment': round(356000 * 0.02), 
            'bid_amount': round(356000 * 1.02)
        },
        'G': {
            'start_price': 356000, 
            'bid_increment': round(356000 * 0.02), 
            'bid_amount': round(356000 * 1.02)
        }
    }
}

@app.route('/')
def index():
    return render_template('index.html', users=users, logged_in_users=logged_in_users)

@app.route('/login/<username>')
def login(username):
    if username not in users:
        logger.warning(f"Login attempt for non-existent user: {username}")
        return "User does not exist."

    logger.info(f"User {username} logged in.")
    logged_in_users[username] = {'bids': 0, 'active': True, 'skips': 2}
    return redirect(url_for('user_panel', username=username))

@app.route('/user/<username>')
def user_panel(username):
        # Check if the user is logged in
    if username not in logged_in_users:
        logger.warning(f"Unauthorized access attempt by user: {username}")
        return redirect(url_for('index'))  # Redirect to the index page


    if not logged_in_users[username]['active']:
        return "You have been excluded from the auction for not bidding in the first round."

    #user_bids = [bid for bid in auction_data['bids'] if bid['user'] == username] # passing bids only made by user
    #user_bids = [bid for bid in auction_data['bids'] ] # passing all bids
    user_bids = [bid for bid in auction_data['bids'] if bid['round'] < auction_data['current_round'] or (bid['user'] == username and bid['round'] == auction_data['current_round'])]

    available_bids = 2
    remaining_time = get_remaining_time()  # Calculate remaining time dynamically
    
    # Calculate sums
    current_lead_blocks = [block for block, leader in auction_data['current_leaders'].items() if leader == username]
    current_sum = sum(auction_data['block_data'][block]['start_price'] for block in current_lead_blocks)
    
    previous_round_bids = [bid for bid in auction_data['bids'] if bid['round'] == auction_data['current_round'] - 1 and bid['user'] == username]
    previous_sum = sum(bid['amount'] for bid in previous_round_bids)

        # Calculate 2% of start price and 1.02 * start price for each block
    for block, data in auction_data['block_data'].items():
        data['default_bid_increment'] = round(data['start_price'] * 0.02, 2)
        data['default_bid_amount'] = round(data['start_price'] * 1.02, 2)

    return render_template('user.html',
                           user=username,
                           auction_data=auction_data,
                           user_bids=user_bids,
                           user_data=logged_in_users[username],
                           available_bids=available_bids,
                           remaining_time=remaining_time,
                           current_sum=current_sum, 
                           previous_sum=previous_sum
                           )

@app.route('/admin')
def admin():
    logger.info("Rendering admin panel.")
    return render_template('admin.html', auction_data=auction_data, logged_in_users=logged_in_users)

@app.route('/start_auction')
def start_auction():
    logger.info("Starting a new auction.")
    auction_data['current_round'] = 1
    auction_data['status'] = 'running'
    auction_data['bids'] = []
    auction_data['results'] = []
    auction_data['current_leaders'] = {block: None for block in ['A', 'B', 'C', 'D', 'E', 'F', 'G']}
    auction_data['round_start_time'] = time.time()  # Record the start time of the auction round
    # Reset start_price and bid_increment to initial values
    initial_start_price = 356000
    initial_bid_increment = 7120
    for block in auction_data['block_data']:
        auction_data['block_data'][block]['start_price'] = initial_start_price
        auction_data['block_data'][block]['bid_increment'] =  initial_bid_increment
    logger.debug(f"Auction data reset: {auction_data}")
    time.sleep(auction_data['round_time'])  # Simulates break duration
    end_round()  # Transition to the end round
    return redirect(url_for('admin'))

@app.route('/place_bid', methods=['POST'])
def place_bid():
    print('bidding ...........')
    user = request.form['user']
    block = request.form['block']
    bid_percentage = int(request.form.get('bid_percentage', 2))  # Default to 2% if not provided
    #amount = auction_data['block_data'][block]['start_price'] + auction_data['block_data'][block]['bid_increment']
    print(f'bid_percentage: {bid_percentage} on block: {block}' )
    start_price = auction_data['block_data'][block]['start_price']
    bid_increment = round(start_price * (bid_percentage / 100))
    amount = round(start_price + bid_increment)

    if logged_in_users[user]['bids'] < 2:
        auction_data['bids'].append({'user': user, 'block': block, 'amount': amount, 'round': auction_data['current_round']})
        logged_in_users[user]['bids'] += 1
        auction_data['current_leaders'][block] = user
        print(f' auction_data: {auction_data}')
        logger.info(f"User {user} placed a bid of {amount} on block {block}.")
        logger.info(f"User auction_data: {auction_data}'")
    else:
        logger.warning(f"User {user} attempted to place a bid but reached their bid limit.")

    return redirect(url_for('user_panel', username=user))

#@app.route('/skip_round/<username>')
#def skip_round(username):
#    if logged_in_users[username]['skips'] > 0:
#        logged_in_users[username]['skips'] -= 1
#        logger.info(f"User {username} skipped the round. Remaining skips: {logged_in_users[username]['skips']}")
#    else:
#        logger.warning(f"User {username} attempted to skip but has no skips left.")
#
#    return redirect(url_for('user_panel', username=username))

@app.route('/skip_round/<username>')
def skip_round(username):
    # Check if the user has skips remaining
    if logged_in_users[username]['skips'] > 0:
        logged_in_users[username]['skips'] -= 1
        logger.info(f"User {username} skipped the round. Remaining skips: {logged_in_users[username]['skips']}")

        # Add a special bid to indicate skipping
        auction_data['bids'].append({
            'user': username,
            'block': 'A',
            'amount': 0,
            'round': auction_data['current_round'],
            'is_success': 'skipped'
        })
    else:
        logger.warning(f"User {username} attempted to skip but has no skips left.")

    return redirect(url_for('user_panel', username=username))

@app.route('/end_round')
def end_round():
    auction_data['status'] = 'break'
    auction_data['current_round'] += 1
    logger.info(f"Round {auction_data['current_round']} ended. Determining winners...")
    determine_winners()
    
    # Update block_data to store bids from the last round
    for block in auction_data['block_data']:
        # Count the number of bids for this block in the last round
        previous_round_bids = [bid for bid in auction_data['bids'] 
                            if bid['round'] == auction_data['current_round'] - 1 
                            and bid['block'] == block]
        auction_data['block_data'][block]['bids_last_round'] = len(previous_round_bids)

    logger.info(f"Bids in the last round per block: {auction_data['block_data']}")
    
    # Check if no bids were placed during the last round
    previous_round_bids = [bid for bid in auction_data['bids'] if bid['round'] == auction_data['current_round'] - 1]
    
    if not previous_round_bids:
        logger.info("No bids were placed during the last round. Ending the auction.")
        auction_data['status'] = 'finished'
        return redirect(url_for('admin'))  # Redirect to the admin panel to show the auction has ended

    update_auction_table()
    auction_data['round_start_time'] = time.time()  # Update the round start time for the new round
    logger.info("Round results updated, auction table refreshed.")
    time.sleep(auction_data['break_time'])  # Simulates break duration
    send_results()  # Transition to the next round
    return redirect(url_for('admin'))

def determine_winners():
    results = {}
    # Only consider bids from the previous round
    previous_round_bids = [bid for bid in auction_data['bids'] if bid['round'] == auction_data['current_round'] - 1]

    for bid in previous_round_bids:
        bid['is_success'] = "no"
        block = bid['block']
        if block not in results:
            results[block] = []
        results[block].append(bid)

    auction_data['results'] = []
    for block, bids in results.items():
        if len(bids) == 0:
            auction_data['current_leaders'][block] = None
        else:
            # Sort bids in descending order of amount
            sorted_bids = sorted(bids, key=lambda x: x['amount'], reverse=True)
            max_amount = sorted_bids[0]['amount']
            highest_bids = [bid for bid in sorted_bids if bid['amount'] == max_amount]

            # Handle ties by selecting a random winner
            if len(highest_bids) > 1:
                winner = random.choice(highest_bids)
            else:
                winner = highest_bids[0]

            for bid in bids:
                if bid == winner:
                    bid['is_success'] = "yes"

            auction_data['results'].append(winner)
            auction_data['current_leaders'][block] = winner['user']


def update_auction_table():
    for result in auction_data['results']:
        block = result['block']
        # Aktualizuj cenę początkową i przyrost dla konkretnego bloku
        auction_data['block_data'][block]['start_price'] = result['amount']
        auction_data['block_data'][block]['bid_increment'] = round(result['amount'] * 0.02)
        logger.debug(f"Updated auction table for block {block}: Start Price = {auction_data['block_data'][block]['start_price']}, Bid Increment = {auction_data['block_data'][block]['bid_increment']}")

@app.route('/send_results')
def send_results():
    auction_data['status'] = 'running'
    
    auction_data['round_start_time'] = time.time()  # Record the start time of the auction round
    for user in logged_in_users:
        logged_in_users[user]['bids'] = 0
    logger.info("Auction results sent and auction reset.")
    time.sleep(auction_data['round_time'])  # Simulates break duration
    end_round()
    return redirect(url_for('admin'))

@app.route('/check_status')
def check_status():
    return jsonify(status=auction_data['status']
                   , round=auction_data['current_round']
                  # , leaders=auction_data['current_leaders']
                   )

def get_remaining_time():
    logger.debug(f"get_remaining_time - pobieranie round_start_time z auction data: {auction_data.get('round_start_time')}")
    logger.info(f"get_remaining_time - pobieranie round_start_time z auction data: {auction_data.get('round_start_time')}")
    print(f"get_remaining_time - pobieranie round_start_time z auction data: {auction_data.get('round_start_time')}")
    
    if 'round_start_time' not in auction_data or auction_data['status'] in ['finished', 'waiting']:
        return 0  # No active round
    
    elapsed_time = time.time() - auction_data['round_start_time']
    print(f" elapsed_time {elapsed_time}")
    if auction_data['status'] == 'running':
        remaining = max(0, auction_data['round_time'] - int(elapsed_time))
    elif auction_data['status'] == 'break':
        remaining = max(0, auction_data['break_time'] - int(elapsed_time))
    else:
        remaining = 0  # Default case if status is unexpected

    # below code is not working due to not refreshing user panel user panel
    # if remaining == 0 and auction_data['status'] == 'running':
    #     print(f" elapsed_remaining {remaining}")
    #     end_round()  # Direct call to the function
    # elif remaining == 0 and auction_data['status'] == 'break':
    #     send_results()  # Direct call to the function
    
    logger.info(f"remaining time: {remaining}")
    return remaining

@app.route('/export_auction_table')
def export_auction_table():
    # Create a CSV file with the auction table
    csv_buffer = io.StringIO()
    writer = csv.writer(csv_buffer)
    writer.writerow(['Block', 'Final Price', 'Winner']) # Header row
    for block, data in auction_data['block_data'].items():
        writer.writerow([block, data['start_price'], auction_data['current_leaders'][block]])

    # Prepare the in-memory file for sending
    csv_buffer.seek(0)  # Move the cursor to the start of the file
    return send_file(
        io.BytesIO(csv_buffer.getvalue().encode('utf-8')),  # Convert StringIO content to bytes
        mimetype='text/csv',
        as_attachment=True,
        download_name=f"auction_table_results.csv"
    )

@app.route('/export_my_bids/<username>')
def export_my_bids(username):
    # Validate the username
    if username not in logged_in_users:
        logger.warning(f"Export attempt for non-existent user: {username}")
        #return abort(404, description="User does not exist.")

    # Filter the user's bids
    user_bids = [bid for bid in auction_data['bids']]
    if not user_bids:
        logger.info(f"No bids found for user: {username}")
        #return abort(404, description="No bids available for export.")

    # Create an in-memory CSV file
    csv_buffer = io.StringIO()
    writer = csv.writer(csv_buffer)
    writer.writerow(['Round', 'Block', 'Amount', 'User', 'Status'])  # Header row
    for bid in user_bids:
        writer.writerow([bid['round'], bid['block'], bid['amount'], bid['user'], bid['is_success']])

    # Prepare the in-memory file for sending
    csv_buffer.seek(0)  # Move the cursor to the start of the file
    return send_file(
        io.BytesIO(csv_buffer.getvalue().encode('utf-8')),  # Convert StringIO content to bytes
        mimetype='text/csv',
        as_attachment=True,
        download_name=f"{username}_bids.csv"
    )

def format_price(price):
    # Zaokrąglij cenę do najbliższej liczby całkowitej
    #price = Decimal(price).quantize(Decimal('1'), rounding=ROUND_DOWN)
    #return format_currency(price, 'PLN', locale='pl_PL')
    formatted_price = format_number(price, locale='pl_PL')
    return f"{formatted_price} zł"
    #return format_currency(price, 'PLN', locale='pl_PL' , currency_digits=False , decimal_quantization=False) , format='#,##0 ¤'

@app.template_filter('format_price')
def format_price_filter(value):
    return format_price(value)

if __name__ == '__main__':
    app.run(debug=False)
