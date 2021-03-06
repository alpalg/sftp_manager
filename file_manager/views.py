from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from .forms import ConnectionForm
from io import BytesIO

from .models import Connection
from pysftp import Connection as SftpConnection
from pysftp import CnOpts, SSHException

CNOPTS = CnOpts()
CNOPTS.hostkeys = None


def index(request):
    """
    Used as main entry point. Propose of registration.
    Redirect if you already logged in.
    :param request: user enter on site.
    :return: 'all_connections' if user authenticated else 'index' page.
    """
    if request.user.is_authenticated:
        return redirect('all_connections')
    return render(request, 'file_manager/index.html')


def user_login(request):
    """
    Logging a user if account exist and entered correct.
    :param request: user want to log into account.
    :return: 'login' page if user not logged and redirect to 'index' page
    if user already logged in.
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user:
            if user.is_active:
                login(request, user)
                return HttpResponseRedirect(reverse('index'))
            else:
                return HttpResponse("Your account was inactive.")
        else:
            return HttpResponse("Invalid login details given")
    else:
        return render(request, 'file_manager/login.html', {})


def user_logout(request):
    """
    Logout and redirect to index page.
    :param request: user want to logout from account.
    :return: redirect to 'index' page.
    """
    logout(request)
    return HttpResponseRedirect(reverse('index'))


def register(request):
    """
    Register of new user.
    :param request: user want ro create a new account.
    :return: 'register' page.
    """
    registered = False
    if request.method == 'POST':
        user_form = UserCreationForm(data=request.POST)
        if user_form.is_valid():
            user = user_form.save()
            user.set_password(user.password)
            user.save()
            registered = True
    else:
        user_form = UserCreationForm()
    return render(request, 'file_manager/register.html',
                  {'user_form': user_form,
                   'registered': registered})


@login_required
def all_connections(request):
    """
    Show all user connection.
    :param request: user starts using SFTP file manager and user
    logged in.
    :return: 'connections' page.
    """
    template = loader.get_template('file_manager/connections.html')
    context = {
        'connections': Connection.objects.filter(user_id=request.user.id)
    }
    return HttpResponse(template.render(context, request))


@login_required
def add_connection(request):
    """
    Create connection. Check connection already exist and valid.
    :param request: user want to add a new SFTP connection.
    :return: 'add_connection' page.
    """
    if request.method == 'POST':
        connection_form = ConnectionForm(data=request.POST)
        host = request.POST.get('host')
        username = request.POST.get('username')
        password = request.POST.get('password')
        try:
            Connection.objects.get(
                user_id=request.user.id,  username=username, host=host)
            return HttpResponse('SFTP Connection already exist.')
        except Connection.DoesNotExist:
            pass
        if connection_form.is_valid():
            try:
                SftpConnection(
                    host, username, password=password, cnopts=CNOPTS)
            except NotADirectoryError:
                return HttpResponse('SFTP Connection cant be established.')
            Connection.objects.create(
                user=request.user,
                host=host,
                username=username,
                password=password)
            return HttpResponseRedirect(reverse('index'))
    else:
        connection_form = ConnectionForm()
    return render(request, 'file_manager/add_connection.html',
                  {'connection_form': connection_form})


@login_required
def edit_connection(request, username, host):
    """
    Edit current connection.
    :param request: user want to edit a SFTP connection.
    :param username: username what used for sftp connection.
    :param host: host what used for sftp connection.
    :return: redirect to 'index' page or render 'edit_connection' page.
    """
    conn = Connection.objects.get(
        user_id=request.user.id, username=username, host=host)
    if request.method != 'POST':
        if conn:
            connection_form = ConnectionForm(instance=conn)
            return render(request, 'file_manager/edit_connection.html',
                          {'connection_form': connection_form})
    else:
        connection_form = ConnectionForm(data=request.POST)
        if connection_form.is_valid():
            host = request.POST.get('host')
            conn.host = host
            conn.username = username
            username = request.POST.get('username')
            conn.password = request.POST.get('password')
            try:
                Connection.objects.get(
                    user_id=request.user.id, username=username, host=host)
                return HttpResponse('SFTP Connection already exist.')
            except Connection.DoesNotExist:
                pass
            conn.save()
        return HttpResponseRedirect(reverse('index'))


@login_required
def delete_connection(request, username, host):
    """
    Delete connection and redirect to index.
    :param request: user want to delete a SFTP connection.
    :param username: username what used for sftp connection.
    :param host: host what used for sftp connection.
    :return: 'index' page/
    """
    conn = Connection.objects.get(
        user_id=request.user.id, username=username, host=host)
    conn.delete()
    return HttpResponseRedirect(reverse('index'))


@login_required
def open_connection(request, username, host, current_dir):
    """
    Used to work with all connections. Create connect and retrieve needed data.
    Connection wasn't saved because need to create connection management
    system bases on session. I think it out of this project.
    :param request: user want open a SFTP connection, or walk dawn to file
        system tree.
    :param username: username what used for sftp connection.
    :param host: host what used for sftp connection.
    :param current_dir: dir where user currently working.
    :return: 'connection' page.
    """
    current_dir = current_dir.replace("^", '/')
    conn = Connection.objects.get(
        user_id=request.user.id, username=username, host=host)
    if conn:
        try:
            with SftpConnection(
                    conn.host, conn.username,
                    password=conn.password, cnopts=CNOPTS) as sftp_conn:
                elms = sftp_conn.listdir_attr(current_dir)
            folders = [
                (f"{current_dir}/{elm.filename}".replace('/', '^'), elm)
                for elm in elms
                if elm.st_size == 0 and not elm.filename.count('.')]
            files = [
                (f"{current_dir}/{elm.filename}".replace('/', '^'), elm)
                for elm in elms
                if elm.st_size > 0 or elm.filename.count('.')]
        except SSHException:
            return HttpResponse('Can`t connect to remote server.')
        template = loader.get_template('file_manager/connections.html')
        previous_dir = ('.' if current_dir == '.' else
                        current_dir[:current_dir.rfind('/')].replace('/', '^'))
        context = {
            'files': files,
            'folders': folders,
            'flagged_connection': conn,
            'current_directory': f"{current_dir}/",
            'previous_dir': previous_dir,
            'connections': Connection.objects.filter(user_id=request.user.id)
        }
        return HttpResponse(template.render(context, request))
    return HttpResponse('Connection impossible.')


@login_required
def get_file(request, username, host, path):
    """
    Download file from via sftp server.
    :param request: user want to download a some file from SFTP server.
    :param username: username what used for sftp connection.
    :param host: host what used for sftp connection.
    :param path: full file path.
    :return: downloaded file.
    """
    path = path.replace("^", '/')
    conn = Connection.objects.get(
        user_id=request.user.id, username=username, host=host)
    stream = BytesIO()
    with SftpConnection(
            conn.host, conn.username,
            password=conn.password, cnopts=CNOPTS) as sftp_conn:
        sftp_conn.getfo(path, stream)
    response = HttpResponse(content_type='application/octet-stream')
    filename = path[path.rfind("/")+1:]
    response['Content-Disposition'] = f'attachment; filename={filename}'
    response.write(stream.getvalue())
    return response
