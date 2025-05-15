import os
import requests
import xml.etree.ElementTree as ET
import logging
from flask import render_template, request, jsonify, session, redirect, url_for, flash
import urllib.parse
from datetime import datetime
import uuid
from models import db, UserSetting
from main import app

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Default API key for National Assembly OpenAPI
DEFAULT_API_KEY = os.environ.get("ASSEMBLY_API_KEY", "aaaadb7517494adf9aa2b11398b3fd76")

# Function to get or create user settings
def get_user_settings():
    # Check if session ID exists
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    
    # Get user settings from database
    user_settings = UserSetting.query.filter_by(session_id=session['session_id']).first()
    
    # If no settings found, create default settings
    if not user_settings:
        user_settings = UserSetting()
        user_settings.session_id = session['session_id']
        user_settings.api_key = DEFAULT_API_KEY
        user_settings.default_assembly_term = "22"
        db.session.add(user_settings)
        db.session.commit()
    
    return user_settings

# National Assembly API endpoints
BILL_API_URL = "https://open.assembly.go.kr/portal/openapi/nzmimeepazxkubdpn"
MEMBER_API_URL = "https://open.assembly.go.kr/portal/openapi/nwvrqwxyaytdsfvhu"

# RSS feed URLs
MOF_RSS_URL = "https://www.moef.go.kr/com/detailRssTagService.do?bbsId=MOSFBBS_000000000028"
FSC_RSS_URL = "http://www.fsc.go.kr/about/fsc_bbs_rss/?fid=0111"

# Naver API settings
NAVER_CLIENT_ID = os.environ.get("NAVER_CLIENT_ID", "MnbrTCUR12n6LKbc_ThO")
NAVER_CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET", "EsAqGMc7zr")
NAVER_NEWS_API_URL = "https://openapi.naver.com/v1/search/news.json"

@app.route('/')
def index():
    """Redirect to the bills search page by default"""
    # Get user settings
    user_settings = get_user_settings()
    
    return render_template('bills.html', 
                           active_tab='bills',
                           assembly_terms=range(17, 23),
                           assembly_term=user_settings.default_assembly_term)

@app.route('/bill', methods=['GET'])
def bill_search():
    """Handle bill search queries"""
    # Get user settings from database
    user_settings = get_user_settings()
    
    # Get parameters from request or use defaults from user settings
    assembly_term = request.args.get('assembly_term', user_settings.default_assembly_term)
    keyword = request.args.get('keyword', '')
    page = int(request.args.get('page', '1'))
    items_per_page = 5  # 고정값으로 설정
    api_key = request.args.get('api_key', user_settings.api_key)
    
    if not keyword:
        return render_template('bills.html', 
                               active_tab='bills',
                               assembly_terms=range(17, 23),
                               assembly_term=assembly_term,
                               bills=[],
                               total_count=0,
                               current_page=page,
                               total_pages=0,
                               keyword=keyword)
    
    # Calculate start index for pagination
    start_index = (page - 1) * items_per_page + 1
    
    # Prepare API request
    params = {
        'KEY': api_key,
        'Type': 'xml',
        'AGE': assembly_term,
        'BILL_NAME': keyword,
        'pIndex': page,
        'pSize': items_per_page
    }
    
    try:
        response = requests.get(BILL_API_URL, params=params)
        
        # Parse XML response
        root = ET.fromstring(response.content)
        
        # Extract data from API response
        bills = []
        total_count = 0
        
        # Get total count from the response
        count_elem = root.find('.//head/list_total_count')
        if count_elem is not None and count_elem.text is not None:
            total_count = int(count_elem.text)
        
        # Get all row elements
        rows = root.findall('.//row')
        
        if rows:
            for row in rows:
                bill_id_elem = row.find('BILL_ID')
                bill_id = bill_id_elem.text if bill_id_elem is not None and bill_id_elem.text is not None else ''
                
                # 안전하게 요소의 텍스트를 가져오는 함수
                def get_elem_text(elem_name):
                    elem = row.find(elem_name)
                    return elem.text if elem is not None and elem.text is not None else ''
                
                # 상태값 가져오기
                proc_result = row.find('PROC_RESULT')
                status = None
                if proc_result is not None and proc_result.text is not None and proc_result.text != 'None':
                    status = proc_result.text
                
                bills.append({
                    'bill_id': bill_id,
                    'bill_no': get_elem_text('BILL_NO'),
                    'bill_name': get_elem_text('BILL_NAME'),
                    'proposer': get_elem_text('PROPOSER'),
                    'propose_date': get_elem_text('PROPOSE_DT'),
                    'committee': get_elem_text('CURR_COMMITTEE'),
                    'status': status,
                    'url': f"https://likms.assembly.go.kr/bill/billDetail.do?billId={bill_id}"
                })
        
        total_pages = (total_count + items_per_page - 1) // items_per_page
        
        return render_template('bills.html', 
                               active_tab='bills',
                               assembly_terms=range(17, 23),
                               assembly_term=assembly_term,
                               bills=bills,
                               total_count=total_count,
                               current_page=page,
                               total_pages=total_pages,
                               keyword=keyword)
    
    except Exception as e:
        logging.error(f"Error fetching bill data: {e}")
        return render_template('bills.html', 
                               active_tab='bills',
                               assembly_terms=range(17, 23),
                               assembly_term=assembly_term,
                               bills=[],
                               error=str(e),
                               keyword=keyword)

@app.route('/member', methods=['GET'])
def member_search():
    """Handle member search queries"""
    # Get user settings from database
    user_settings = get_user_settings()
    
    # Get parameters from request or use defaults from user settings
    assembly_term = request.args.get('assembly_term', user_settings.default_assembly_term)
    keyword = request.args.get('keyword', '')
    api_key = request.args.get('api_key', user_settings.api_key)
    
    if not keyword:
        return render_template('members.html', 
                               active_tab='members',
                               assembly_terms=range(17, 23),
                               assembly_term=assembly_term,
                               members=[],
                               keyword=keyword)
    
    # Prepare API request
    params = {
        'KEY': api_key,
        'Type': 'xml',
        'AGE': assembly_term,
        'HG_NM': keyword,
        'pIndex': 1,
        'pSize': 50  # Get more results for members as the total count is typically small
    }
    
    try:
        response = requests.get(MEMBER_API_URL, params=params)
        
        # Parse XML response
        root = ET.fromstring(response.content)
        
        # Extract data from API response
        members = []
        
        # Get all row elements
        rows = root.findall('.//row')
        
        if rows:
            for row in rows:
                # 안전하게 요소의 텍스트를 가져오는 함수
                def get_elem_text(elem_name):
                    elem = row.find(elem_name)
                    return elem.text if elem is not None and elem.text is not None else ''
                
                assem_addr = get_elem_text('ASSEM_ADDR')
                members.append({
                    'name': get_elem_text('HG_NM'),
                    'party': get_elem_text('POLY_NM'),
                    'district': get_elem_text('ORIG_NM'),
                    'committee': get_elem_text('CMIT_NM'),
                    'elected_times': get_elem_text('REELE_GBN_NM'),
                    'birthday': get_elem_text('BTH_DATE'),
                    'photo_url': get_elem_text('HJ_URL'),
                    'profile_url': f"https://www.assembly.go.kr/assm/memPop/memPopup.do?dept_cd={assem_addr}"
                })
        
        return render_template('members.html', 
                               active_tab='members',
                               assembly_terms=range(17, 23),
                               assembly_term=assembly_term,
                               members=members,
                               keyword=keyword)
    
    except Exception as e:
        logging.error(f"Error fetching member data: {e}")
        return render_template('members.html', 
                               active_tab='members',
                               assembly_terms=range(17, 23),
                               assembly_term=assembly_term,
                               members=[],
                               error=str(e),
                               keyword=keyword)

@app.route('/press/mof', methods=['GET'])
def press_mof():
    """Handle Ministry of Economy and Finance press release queries"""
    page = int(request.args.get('page', '1'))
    items_per_page = 5  # 고정값으로 설정
    
    try:
        response = requests.get(MOF_RSS_URL)
        
        # Parse XML
        root = ET.fromstring(response.content)
        
        # Extract items from RSS feed
        items = []
        for item in root.findall('.//item'):
            # 안전하게 요소의 텍스트를 가져오는 함수
            def get_elem_text(elem_name):
                elem = item.find(elem_name)
                return elem.text if elem is not None and elem.text is not None else ''
            
            title = get_elem_text('title')
            link = get_elem_text('link')
            pub_date_text = get_elem_text('pubDate')
            description = get_elem_text('description')
            
            # Parse and format the publication date
            formatted_date = ''
            try:
                if pub_date_text:
                    pub_date = datetime.strptime(pub_date_text, '%a, %d %b %Y %H:%M:%S %z')
                    formatted_date = pub_date.strftime('%Y-%m-%d')
                else:
                    formatted_date = ''
            except:
                formatted_date = pub_date_text
            
            items.append({
                'title': title,
                'link': link,
                'pub_date': formatted_date,
                'description': description
            })
        
        # Implement pagination
        start_idx = (page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        paginated_items = items[start_idx:end_idx]
        total_count = len(items)
        total_pages = (total_count + items_per_page - 1) // items_per_page
        
        return render_template('press_mof.html', 
                               active_tab='mof',
                               items=paginated_items,
                               total_count=total_count,
                               current_page=page,
                               total_pages=total_pages)
    
    except Exception as e:
        logging.error(f"Error fetching MOF press releases: {e}")
        return render_template('press_mof.html', 
                               active_tab='mof',
                               items=[],
                               error=str(e))

@app.route('/press/fsc', methods=['GET'])
def press_fsc():
    """Handle Financial Services Commission press release queries"""
    page = int(request.args.get('page', '1'))
    items_per_page = int(request.args.get('items_per_page', '5'))
    
    try:
        response = requests.get(FSC_RSS_URL)
        
        # Parse XML
        root = ET.fromstring(response.content)
        
        # Register DC namespace for handling dc:date
        namespaces = {'dc': 'http://purl.org/dc/elements/1.1/'}
        
        # Extract items from RSS feed
        items = []
        for item in root.findall('.//item'):
            # 안전하게 요소의 텍스트를 가져오는 함수
            def get_elem_text(elem_name):
                elem = item.find(elem_name)
                return elem.text if elem is not None and elem.text is not None else ''
            
            title = get_elem_text('title')
            link = get_elem_text('link')
            
            # Try to get dc:date first, then fallback to pubDate
            dc_date_elem = item.find('.//dc:date', namespaces)
            pub_date_text = ''
            if dc_date_elem is not None and dc_date_elem.text is not None:
                pub_date_text = dc_date_elem.text
            else:
                pub_date_elem = item.find('pubDate')
                if pub_date_elem is not None and pub_date_elem.text is not None:
                    pub_date_text = pub_date_elem.text
            
            description = get_elem_text('description')
            
            # Parse and format the publication date
            formatted_date = ''
            if pub_date_text:
                try:
                    # Try ISO format (for dc:date)
                    try:
                        pub_date = datetime.fromisoformat(pub_date_text.replace('Z', '+00:00'))
                        formatted_date = pub_date.strftime('%Y-%m-%d')
                    except ValueError:
                        # Try RSS format (for pubDate)
                        pub_date = datetime.strptime(pub_date_text, '%a, %d %b %Y %H:%M:%S %z')
                        formatted_date = pub_date.strftime('%Y-%m-%d')
                except:
                    formatted_date = pub_date_text
            
            items.append({
                'title': title,
                'link': link,
                'pub_date': formatted_date,
                'description': description
            })
        
        # Implement pagination
        start_idx = (page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        paginated_items = items[start_idx:end_idx]
        total_count = len(items)
        total_pages = (total_count + items_per_page - 1) // items_per_page
        
        return render_template('press_fsc.html', 
                               active_tab='fsc',
                               items=paginated_items,
                               total_count=total_count,
                               current_page=page,
                               total_pages=total_pages)
    
    except Exception as e:
        logging.error(f"Error fetching FSC press releases: {e}")
        return render_template('press_fsc.html', 
                               active_tab='fsc',
                               items=[],
                               error=str(e))

@app.route('/news', methods=['GET'])
def news_search():
    """Handle Naver News search queries"""
    keyword = request.args.get('keyword', '')
    page = int(request.args.get('page', '1'))
    items_per_page = 5  # Fixed at 5 items per page
    
    if not keyword:
        return render_template('news.html', 
                               active_tab='news',
                               news_items=[],
                               keyword='')
    
    try:
        # Prepare API request
        headers = {
            'X-Naver-Client-Id': NAVER_CLIENT_ID,
            'X-Naver-Client-Secret': NAVER_CLIENT_SECRET
        }
        
        params = {
            'query': keyword,
            'display': 100,  # Get more results to handle pagination
            'start': 1,
            'sort': 'date'
        }
        
        response = requests.get(NAVER_NEWS_API_URL, headers=headers, params=params)
        
        if response.status_code != 200:
            raise Exception(f"API Error: {response.status_code}")
        
        # Parse JSON response
        json_data = response.json()
        
        total_results = min(json_data.get('total', 0), len(json_data.get('items', [])))
        
        if total_results == 0:
            return render_template('news.html', 
                                   active_tab='news',
                                   news_items=[],
                                   keyword=keyword,
                                   message="검색 결과가 없습니다.")
        
        # Process all items to clean HTML entities
        news_items = []
        for item in json_data.get('items', []):
            # Clean HTML tags and entities
            title = item.get('title', '')
            description = item.get('description', '')
            
            # Remove HTML tags and entities
            for html_field, repl_field in [('<b>', ''), ('</b>', ''), ('&quot;', '"'), 
                                        ('&apos;', "'"), ('&lt;', '<'), ('&gt;', '>'), 
                                        ('&amp;', '&')]:
                title = title.replace(html_field, repl_field)
                description = description.replace(html_field, repl_field)
            
            # Format date
            pub_date = item.get('pubDate', '')
            try:
                pub_date_obj = datetime.strptime(pub_date, '%a, %d %b %Y %H:%M:%S %z')
                formatted_date = pub_date_obj.strftime('%Y-%m-%d')
            except:
                formatted_date = pub_date
                
            news_items.append({
                'title': title,
                'description': description,
                'link': item.get('link', ''),
                'pub_date': formatted_date,
                'original_link': item.get('originallink', '')
            })
        
        # Implement pagination
        start_idx = (page - 1) * items_per_page
        end_idx = min(start_idx + items_per_page, total_results)
        paginated_items = news_items[start_idx:end_idx]
        
        total_pages = (total_results + items_per_page - 1) // items_per_page
        
        return render_template('news.html', 
                               active_tab='news',
                               news_items=paginated_items,
                               total_count=total_results,
                               current_page=page,
                               total_pages=total_pages,
                               keyword=keyword)
        
    except Exception as e:
        logging.error(f"Error fetching news data: {e}")
        return render_template('news.html', 
                               active_tab='news',
                               news_items=[],
                               error=str(e),
                               keyword=keyword)

@app.route('/central_bank', methods=['GET'])
def central_bank_laws():
    """Handle central bank laws page"""
    return render_template('central_bank.html', 
                           active_tab='central_bank')

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    """Handle settings page"""
    # Get user settings from database
    user_settings = get_user_settings()
    
    if request.method == 'POST':
        # Update user settings
        api_key = request.form.get('api_key', DEFAULT_API_KEY)
        assembly_term = request.form.get('default_assembly_term', '22')
        
        # Save to database
        user_settings.api_key = api_key
        user_settings.default_assembly_term = assembly_term
        db.session.commit()
        
        flash('설정이 저장되었습니다.', 'success')
        return redirect(url_for('settings'))
    
    return render_template('settings.html', 
                           active_tab='settings',
                           assembly_terms=range(17, 23),
                           default_api_key=user_settings.api_key,
                           default_assembly_term=user_settings.default_assembly_term)

@app.template_filter('truncate_text')
def truncate_text(text, length=100):
    """Template filter to truncate text to a specified length"""
    if not text:
        return ""
    if len(text) <= length:
        return text
    return text[:length] + '...'

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
