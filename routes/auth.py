from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from config.supabase_config import supabase
import uuid
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

auth = Blueprint('auth', __name__)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name')
        role = request.form.get('role', 'worker')  # Default role is worker
        
        # Check if user already exists
        try:
            existing_user = supabase.table('users').select('*').eq('email', email).execute()
            if existing_user.data:
                flash('Email already registered', 'error')
                return redirect(url_for('auth.register'))
            
            # Create new user
            new_user = {
                'uid': str(uuid.uuid4()),
                'email': email,
                'password_hash': generate_password_hash(password),
                'name': name,
                'role': role
            }
            
            result = supabase.table('users').insert(new_user).execute()
            
            if result.data:
                flash('Registration successful! Please login.', 'success')
                return redirect(url_for('auth.login'))
            else:
                flash('Registration failed. Please try again.', 'error')
                
        except Exception as e:
            flash(f'Error during registration: {str(e)}', 'error')
            
    return render_template('auth/register.html')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        logger.debug(f"Login attempt for email: {email}")
        
        try:
            # Get user by email
            result = supabase.table('users').select('*').eq('email', email).execute()
            logger.debug(f"Supabase query result: {result}")
            
            if result.data and len(result.data) > 0:
                user = result.data[0]
                logger.debug(f"Found user: {user}")
                
                if check_password_hash(user['password_hash'], password):
                    logger.debug("Password check passed")
                    # Store user info in session
                    session['user'] = {
                        'id': user['uid'],  # Use uid instead of id
                        'email': user['email'],
                        'name': user['name'],
                        'role': user['role']
                    }
                    logger.debug(f"Session data set: {session['user']}")
                    
                    # Redirect based on role
                    if user['role'] == 'admin':
                        logger.debug("Redirecting to admin dashboard")
                        return redirect(url_for('admin.admin_dashboard'))
                    elif user['role'] == 'supervisor':
                        logger.debug("Redirecting to supervisor dashboard")
                        return redirect(url_for('supervisor.supervisor_dashboard'))
                    elif user['role'] == 'worker':
                        logger.debug("Redirecting to worker dashboard")
                        return redirect(url_for('worker.dashboard'))
                    elif user['role'] == 'client':
                        logger.debug("Redirecting to client dashboard")
                        return redirect(url_for('client.dashboard'))
                else:
                    logger.debug("Invalid password")
                    flash('Invalid password', 'error')
            else:
                logger.debug("User not found")
                flash('User not found', 'error')
                
        except Exception as e:
            logger.error(f"Error during login: {str(e)}", exc_info=True)
            flash(f'Error during login: {str(e)}', 'error')
            
    return render_template('auth/login.html')

@auth.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('auth.login'))


