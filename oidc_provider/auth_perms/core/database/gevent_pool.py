from gevent.queue import Queue
from gevent.socket import wait_read, wait_write
from psycopg2 import extensions, OperationalError, connect
from psycopg2.extensions import connection as connection_type


def gevent_callback(conn: connection_type, timeout: int = None) -> None:
    """
    Makes psycopg gevent friendly
    """
    while True:
        state = conn.poll()
        if state == extensions.POLL_OK:
            break
        elif state == extensions.POLL_READ:
            wait_read(conn.fileno(), timeout=timeout)
        elif state == extensions.POLL_WRITE:
            wait_write(conn.fileno(), timeout=timeout)
        else:
            raise OperationalError()


class GeventFriendlyConnectionPool:
    """ 
    NOTE: This connection pool must be used only with Gevent mode
    """

    def __init__(self, minconn: int, maxconn: int, *args, **kwargs) -> None:
        self.maxconn = maxconn
        self.minconn = minconn
        self.args = args
        self.kwargs = kwargs
        self.size = 0
        self.pool = Queue()
        extensions.set_wait_callback(gevent_callback)
        for i in range(self.minconn):
            self.create_connection()

    def getconn(self) -> connection_type:
        if self.size >= self.maxconn or self.pool.qsize():
            return self.pool.get()
        self.size += 1
        try:
            conn = self.create_connection()
        except Exception:
            self.size -= 1
            raise
        return conn

    def create_connection(self):
        return connect(*self.args, **self.kwargs)

    def putconn(self, conn: connection_type) -> None:
        try:
            self._putconn(conn)
        except Exception:
            conn.close()

    def _putconn(self, conn: connection_type, close: bool = False) -> None:
        if self.pool.qsize() < self.minconn:
            if not conn.closed:
                status = conn.info.transaction_status
                if status == extensions.TRANSACTION_STATUS_UNKNOWN:
                    # problem with server
                    conn.close()
                elif status != extensions.TRANSACTION_STATUS_IDLE:
                    # some error in transaction
                    conn.rollback()
                    self.pool.put(conn)
                else:
                    # idle
                    self.pool.put(conn)
        if close:
            conn.close()

    def closeall(self) -> None:
         while not self.pool.empty():
            conn = self.pool.get_nowait()
            try:
                conn.close()
            except Exception:
                pass