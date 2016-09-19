# coding=utf-8
__author__ = 'willi'

from flask import Flask, render_template, request, jsonify, session, abort, flash
from flask.ext.basicauth import BasicAuth
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.sql.expression import func, between, or_
from database import Comparison, Result
from datetime import datetime, timedelta, date
import random
import string

########################################################################################################################
# Config
########################################################################################################################

app = Flask(__name__)
app.config['DEBUG'] = False
app.config['DATABASE_URL'] = 'sqlite:///database/tlscompare.db'

# Used a flask extension for basic auth
# https://flask-basicauth.readthedocs.org/en/latest/
app.config['BASIC_AUTH_USERNAME'] = 'superadmin'
app.config['BASIC_AUTH_PASSWORD'] = 'this-is-the-best-password-evar'
basic_auth = BasicAuth(app)

app.config['DATASETS'] = ['generated-around-threshold',
                          'generated-valid-top10k',
                          'existing',
                          'pets-ws15']
app.config['DATASET_DEFAULT'] = 'generated-valid-top10k'

app.config['NEG_REASONS'] = ['mixed-content',
                             'certificate-mismatch',
                             'timeout',
                             'untrusted-certificate',
                             'no-sense']
app.config['POS_REASONS'] = ['mixed-content',
                             'sense']

# This secret key is for encrypting the cookies
app.secret_key = 'here-should-be-a-secret-key-for-cookie-encryption'

########################################################################################################################
# Web Code
########################################################################################################################

dbsession = None


@app.route('/')
def index():
    """
    The default comparison page
    """
    check_datset()
    check_uid()

    # Get new random comparison
    return render_template('comparison.html', counter=get_result_count_for_uid(session['id']))


@app.route('/expert')
def expert():
    """
    Expert page, same as comparison, but expert.html
    """
    check_datset()
    check_uid()

    # Get new random comparison
    return render_template('expert.html', counter=get_result_count_for_uid(session['id']))


@app.route('/invalid/<req_id>', methods=['GET'])
def invalid(req_id):
    """
    Mark a rule as invalid
    reason checked
    req_id checked
    """
    try:
        int(req_id)
    except ValueError:
        abort(403)

    if 'id' not in session or session['id'] == "":
        abort(403)
    else:
        reason = request.args.get('reason', None)

        if reason is not None and reason not in app.config['NEG_REASONS']:
            abort(403)
        ret = save_result(session['id'], req_id, False, reason=reason)
        if not ret:
            abort(403)
        return "", 200


@app.route('/valid/<req_id>', methods=['GET'])
def valid(req_id):
    """
    Mark a rule as valid
    req_id checked
    reason checked
    """
    try:
        int(req_id)
    except ValueError:
        abort(403)

    if 'id' not in session or session['id'] == "":
        abort(403)
    else:
        reason = request.args.get('reason', None)
        if reason is not None and reason not in app.config['POS_REASONS']:
            abort(403)
        ret = save_result(session['id'], req_id, True, reason=reason)
        if not ret:
            abort(403)
        return "", 200


@app.route('/overview')
def overview():
    """
    Statistics
    """
    check_datset()
    check_uid()

    return render_template('overview.html',
                           hours_wasted=get_hours_wasted(),
                           hourly_stats=get_results_hourly(),
                           daily_stats=get_results_daily(),
                           nr_results_id=get_result_count_for_uid(session['id']),
                           nr_results_ip=get_result_count_for_ip(request.remote_addr),
                           nr_comparisons=dbsession.query(Comparison).count(),
                           nr_results=dbsession.query(Result).count(),
                           # false_pos=get_false_pos_query().count(),
                           # false_neg=get_false_neg_query().count(),
                           nr_current_dataset=get_dataset(session['dataset']).count(),
                           dataset=session['dataset'])


@app.route('/comparison')
def get_random_comparison_json():

    check_uid()
    check_datset()

    query = dbsession.query(Comparison, func.count(Result.id).label('c'))
    subquery = filter_dataset(query, session['dataset']).outerjoin(Result).group_by(Comparison.id).subquery()
    min_results = dbsession.query(func.min(subquery.c.c)).scalar()
    comp = get_dataset(session['dataset']).outerjoin(Result).group_by(Comparison.id).having(func.count(Result.id) == min_results).order_by(func.random()).first()

    req_id = generate_request(session['id'], comp.id)

    return jsonify({'http_url': comp.http_url, 'https_url': comp.https_url, 'rid': req_id})


@app.route('/dataset/<dataset_id>', methods=['GET'])
def set_dataset(dataset_id):
    """
    Change a dataset in the session
    dataset_id checked
    """
    if dataset_id in app.config['DATASETS']:
        session['dataset'] = dataset_id
        return dataset_id
    else:
        abort(403)

@app.route('/student/<matnr>', methods=['GET'])
def set_student(matnr):
    """
    Set the matnr to the session
        This is only allowed once per session -> Otherwise the student has to close the browser and do it again
        It takes matnr up to 16 chars -> we could use other ids instead of matnr
    Then set the dataset to pets-ws15
       matnr overwrites other dataset settings, see check_datset()
       the filter of pets-ws15 is defined in filter_dataset()
    """

    check_uid()

    if 'matnr' not in session or session['matnr'] == "":
        session['matnr'] = matnr[:16]

    session['dataset'] = 'pets-ws15'

    return render_template('expert.html', counter=get_result_count_for_uid(session['id']))

@app.route('/student/logout')
def logout():
    session.clear()
    return index()

@app.route('/contact')
def contact():
    return render_template('contact.html')


@app.route('/faq')
def faq():
    return render_template('faq.html')


@app.route('/admin')
@basic_auth.required
def admin():
    return render_template('admin.html')


@app.route('/results', defaults={'cid': None})
@app.route('/results/<cid>')
@basic_auth.required
def results(cid):

    try:
        if cid is not None:
            int(cid)
    except ValueError:
        abort(403)

    page = int(request.args.get('page', 0))
    q = dbsession.query(Result).join(Comparison)

    comparison = False
    if cid:
        q = q.filter(Result.comparison_id == cid)
        comparison = True

    count = q.count()
    q = q.limit(100).offset(100*page)

    return render_template('results.html',
                           stats=q.all(),
                           comparison=comparison,
                           pos_reasons=app.config['POS_REASONS'],
                           neg_reasons=app.config['NEG_REASONS'],
                           count=count,
                           page=page)


# @app.route('/results/false_pos')
# @basic_auth.required
# def results_false_pos():
#     return render_template('results.html',
#                            stats=get_false_pos_query().all(),
#                            comparison=False,
#                            pos_reasons=app.config['POS_REASONS'],
#                            neg_reasons=app.config['NEG_REASONS'])
#
#
# @app.route('/results/false_neg')
# @basic_auth.required
# def results_false_neg():
#     return render_template('results.html',
#                            stats=get_false_neg_query().all(),
#                            comparison=False,
#                            pos_reasons=app.config['POS_REASONS'],
#                            neg_reasons=app.config['NEG_REASONS'])


@app.route('/change_reason/<req_id>', methods=['GET'])
@basic_auth.required
def change_reason(req_id):
    """
    Change a reason afterwards (from results page)
    req_id checked
    reason checked
    """
    try:
        int(req_id)
    except ValueError:
        abort(403)

    reason = request.args.get('reason', None)
    if reason is not None and reason not in app.config['NEG_REASONS'] and reason not in app.config['POS_REASONS']:
        abort(403)

    ret = change_reason_result(req_id, reason)
    if not ret:
        abort(403)
    return "", 200


########################################################################################################################
# Helper (DB and so on)
########################################################################################################################


# def get_false_pos_query():
#     return dbsession.query(Result).join(Comparison) \
#         .filter(Result.validity.is_(False)) \
#         .filter(Comparison.similarityvalue1 > THRESHOLD_SIMILARITYVALUE1) \
#         .filter(Comparison.similarityvalue2 > THRESHOLD_SIMILARITYVALUE2)
#
#
# def get_false_neg_query():
#     return dbsession.query(Result).join(Comparison)\
#         .filter(Result.validity.is_(True))\
#         .filter(Comparison.similarityvalue1 <= THRESHOLD_SIMILARITYVALUE1)\
#         .filter(Comparison.similarityvalue2 <= THRESHOLD_SIMILARITYVALUE2)

@app.route('/dataset_stats')
@basic_auth.required
def dataset_stats():

    datasets = []

    for dataset in app.config['DATASETS']:

        query = dbsession.query(Comparison, func.count(Result.id).label('c'))
        subquery = filter_dataset(query, dataset).outerjoin(Result).group_by(Comparison.id).subquery()
        nr_results = dbsession.query(subquery.c.c, func.count('*')).group_by(subquery.c.c).all()

        datasets.append({'name': dataset,
                         'nr_comparisons': get_dataset(dataset).count(),
                         'nr_results': nr_results})

    return render_template('datasetstat.html',
                           datasets=datasets)


def generate_request(uid, cid):
    r = Result(uid=uid,
               comparison_id=cid,
               req_time=datetime.now(),
               ip=request.remote_addr,
               useragent=str(request.user_agent))

    if 'matnr' in session:
        r.matnr = session['matnr']

    dbsession.add(r)
    dbsession.commit()
    return r.id


def save_result(uid, request_id, validity, reason=None):
    r = dbsession.query(Result).filter_by(id=request_id).first()
    if r is None:
        return False
    else:
        if r.validity is not None or \
                r.uid != uid or \
                r.ip != request.remote_addr or \
                r.useragent != str(request.user_agent):
            return False
        if 'matnr' in session and r.matnr != session['matnr'] or \
           'matnr' not in session and r.matnr is not None:
            return False

        r.res_time = datetime.now()
        r.validity = validity

        if r.validity is True and reason is not None and reason not in app.config['POS_REASONS']:
            return False
        elif r.validity is False and reason is not None and reason not in app.config['NEG_REASONS']:
            return False

        r.reason = reason

        dbsession.commit()
        return True


def change_reason_result(request_id, reason):
    r = dbsession.query(Result).filter_by(id=request_id).first()

    if r.validity is True and reason is not None and reason not in app.config['POS_REASONS']:
        return False
    elif r.validity is False and reason is not None and reason not in app.config['NEG_REASONS']:
        return False

    r.reason = reason
    r.reason_changed = True

    dbsession.commit()
    return True


def get_result_count_for_uid(uid):
    """
    Return the current results on the start page
    if matnr is set in session, use this
    :param uid:
    :return:
    """
    if 'matnr' in session:
        return dbsession.query(Result).filter(Result.validity.isnot(None)).filter(Result.matnr == session['matnr']).count()
    else:
        return dbsession.query(Result).filter(Result.validity.isnot(None)).filter(Result.uid == uid).count()


def get_result_count_for_ip(ip):
    return dbsession.query(Result).filter(Result.validity.isnot(None)).filter(Result.ip == ip).count()


def get_results_daily():
    values = dbsession.query(func.date(Result.res_time).label('date'), func.count("*").label('count'))\
                      .filter(Result.validity.isnot(None))\
                      .filter(Result.res_time > (date.today()-timedelta(days=30)))\
                      .group_by('date').all()
    return values


def get_results_hourly():
    values = dbsession.query(func.strftime('%H', Result.res_time).label('date'), func.count("*").label('count'))\
                      .filter(Result.validity.isnot(None))\
                      .group_by('date').all()

    d = {n: 0 for n in range(24)}
    for hour, count in values:
        d[int(hour)] = count
    return d


def get_hours_wasted():
    return round(dbsession.query(func.sum(func.strftime('%s', Result.res_time)-func.strftime('%s', Result.req_time)))
                          .filter(Result.validity.isnot(None)).first()[0]/3600.0, 3)


def check_uid():
    if 'id' not in session or session['id'] == "":
        session['id'] = get_random_id()

########################################################################################################################
# Datasets
########################################################################################################################

THRESHOLD_SIMILARITYVALUE1 = 0.49
THRESHOLD_SIMILARITYVALUE2 = 0.68


def check_datset():
    if 'matnr' in session:
        session['dataset'] = 'pets-ws15'
    if 'dataset' not in session:
        session['dataset'] = app.config['DATASET_DEFAULT']


def get_dataset(dataset):
    return filter_dataset(dbsession.query(Comparison), dataset)


def filter_dataset(query, dataset):
    # Only https everywhere
    if dataset == "existing":
        return query.filter(Comparison.code == "H").order_by(func.random())
    # around-threshold
    # where similarityvalue1 BETWEEN 0.39 and 0.59
    #    or similarityvalue2 BETWEEN 0.58 and 0.77
    # and ruleset of dominik
    elif dataset == "generated-around-threshold":
        return query.filter(Comparison.code == "D") \
            .filter(or_(between(Comparison.similarityvalue1,
                                THRESHOLD_SIMILARITYVALUE1 - 0.1,
                                THRESHOLD_SIMILARITYVALUE1 + 0.1),
                        between(Comparison.similarityvalue2,
                                THRESHOLD_SIMILARITYVALUE2 - 0.1,
                                THRESHOLD_SIMILARITYVALUE2 + 0.1))) \
            .filter(Comparison.http_url.like('http://%/')) \
            .filter(Comparison.https_url.like('https://%/')) \
            .order_by(func.random())
    elif dataset == "generated-valid-top10k":
        return query.filter(Comparison.code == "D") \
            .filter(Comparison.similarityvalue1 >= 0.95) \
            .filter(Comparison.similarityvalue2 >= 0.95) \
            .filter(Comparison.http_url.like('http://%/')) \
            .filter(Comparison.https_url.like('https://%/')) \
            .filter(Comparison.rank < 48890) \
            .order_by(func.random())
    # Pure Random
    elif dataset == "pets-ws15":
        return query.filter(Comparison.code == "PETS-WS15").order_by(func.random())
    else:
        return query.order_by(func.random())


def get_random_id():
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(32))


@app.before_request
def create_session():
    global dbsession
    if dbsession is None:
        engine = create_engine(app.config['DATABASE_URL'])
        dbsession = scoped_session(sessionmaker(bind=engine))


@app.teardown_appcontext
def shutdown_session(_=None):
    global dbsession
    if dbsession is not None:
        dbsession.remove()
    dbsession = None

if __name__ == '__main__':
    app.run()
