import sys, threading, time, logging

#################################################
## an example of a retryable decorator
## see README for details.
#################################################

# some exceptions
class ConnectionError(Exception):
    pass

class SomeOtherError(Exception):
    pass


# retryable decorator.  it either expects a stoppable object or will look in the func parameters
def retryable(retry_frequency_seconds, retryable_exceptions, max_tries=0, stop_object=None):

    def wrap(f):

        def func(*args, **kwargs):

            count = 0
            retry_forever = max_tries <= 0
            last_exception = None
            should_stop = False
            stoppable_object = stop_object or args[0]

            # TODO: probably should verify stoppable_object is really stoppable.

            while not should_stop:
                try:
                    return f(*args, **kwargs)
                except retryable_exceptions:
                    logging.exception("caught retryable exception")
                    count = count + 1

                if not stoppable_object.stopped:

                    try:
                        logging.debug("sleeping %d seconds before retrying (attempt=%d)..." % (retry_frequency_seconds, count))
                        stoppable_object.stop_condition.acquire()
                        stoppable_object.stop_condition.wait(retry_frequency_seconds)
                    finally:
                        stoppable_object.stop_condition.release()

                should_stop = stoppable_object.stopped or (count >= max_tries and not retry_forever)
            raise last_exception

        return func

    return wrap

# object with a stop condition.
class Stoppable(object):
    stopped = False
    stop_condition = threading.Condition()

    def stop(self):
        logging.debug("Stop requested")
        self.stopped = True
        try:
            self.stop_condition.acquire()
            self.stop_condition.notify_all()
        finally:
            self.stop_condition.release()


# this would represent your core code.
class MainThread(threading.Thread, Stoppable):
    i = 0

    def __init__(self):
        threading.Thread.__init__(self)



    @retryable(10, (ConnectionError, SomeOtherError))
    def get_job_from_database (self):

        """ Pretend this represents retrieval of job data from a database.  A ConnectionError or SomeOtherError
        is a valid retryable exception.  """

        logging.info("i=%d" % self.i)
        if self.i < 3:
            raise ConnectionError("I'm a connection exception - please retry on this.")
        if self.i < 6:
            raise SomeOtherError("I'm some other error that is ok to retry.")
        elif self.i < 9:
            return "job%d" % self.i
        else:
            raise Exception("this is not caught and will explode")


    def run(self):
        """ hello, I do stuff in a loop, like look for new jobs to run."""
        try:
            while (not self.stopped):
                self.i = self.i + 1
                job = self.get_job_from_database()

                if (job):
                    # TODO: now do something with that job. make more db operations, etc.
                    print job

                try:
                   self.stop_condition.acquire()
                   self.stop_condition.wait(10) # sleep 10 seconds.
                except: # can be interrupted legitimately.
                   pass
                finally:
                   self.stop_condition.release()


        except:
            logging.exception("uh oh, there's an uncaught error.  I better notify my maintainers...")
        finally:
            print "stopped"


def debug_start():
    fmt = "%(asctime)-15s %(levelname)s [%(module)s] %(message)s"
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format=fmt)
    main = MainThread()
    main.start()
    return main

#start

main = debug_start()
try:
    while main.is_alive():
        time.sleep(60)
except KeyboardInterrupt:
    main.stop()

main.join()