
In short:
=========
This code represents an example of a retry pattern I'm testing out.

To make a method retryable, just add the @retryable decorator:

    @retryable(<retry frequency seconds>,(<exception_that_can_be_retried>, ), [max_retries],[stop_object])

e.g.:
 
    # retries every 60 seconds every time there is a connection error.
    @retryable(60, (ConnectionError,))
    def function(self):
         ... 

By retryable, I mean that if one of the expected "retryable" exceptions, the function will not throw it - it will simply retry for as long as it can, sleeping for <retry frequence seconds> in between.  A successful function call will return the results as expected.  

if, for some reason, the function never succeeds (say, the # of tries exceeds the max_retries) we'll just throw up the last exception that caused the issue.

note: a failure must be represented by an exception in the current pattern example.  code changes will need to be made if you want the decorator to check for bad return values.


**details:**

 * "stop_object" is used to determine when to stop retrying (if the main program receives a shutdown message, for example).  it must have two properties, a boolean "stopped" and a threading.Condition stop_condition

 * max_retries is a high limit of the # of retries to make. to retry forever, set max_retries=0


Enjoy!

-Jen

jandre@gmail.com


Of course, after I wrote this I used google and found this other nice example as well:

- http://www.saltycrane.com/blog/2009/11/trying-out-retry-decorator-python/



Long Story:
===========
I was thinking today about making this code I'm writing more robust.  Like a lot of enterprise code, the thing I am working on now has several external dependencies (database, web services) and in the middle of processing what represents a single job, or transaction, updates are made in several places (update tables, make a web service call). Naturally, I have to think about what happens if in the middle of such a job, a database connection fails, or the users requests a shutdown, how do we handle these things gracefully?  We don't want to leave things in a statewhere the data is bad.  Also, it would be lovely if the program didn't crash simply because it can't hit a database for a few seconds.

In the shutdown scenario, my solution is simply: I won't shut down until the job is complete.  I use a thread/stop pattern to accomplish this generally -- the user requests a stop, but the working thread only at certain points will check to see if a stop is requested (e.g. after a job is complete -- however, this is somewhat of an art, as you have to be careful not to block shutdown forever, ideally not more than for a few seconds).  Any failure to shut down gracefully should notify the maintainers (e.g., send an email notification).

For the database/web service/x scenario, you have a couple of options.  You can build some kind of transaction coordinator that keeps track of changes you've made with the corresponding rollbacks but this doesn't really help you in a scenario like this:

<pre>
    job:
        1) call webmethod x on webservice "a"
        2) call webmethod y on webservice "a"
</pre>

...if step 2 fails with a connection failure because webservice a is suddenly unavailable, you can't run the rollback
immediately.

In this scenario, on failure to call webmethod a in step 2, it would be nice if the code waited a while, then retried again to see if the webservice was available again.  This could happen indefinitely, until someone requested the program were stopped.   A stop (or a max_limit reached on the # of retries) basically bubbles the exception up to be handled by the main loop, which should have some general "catch all" that can do something meaningful with that error (email someone).

Python fortunately has some very nice language constructs to accomplish all of this, hence this code I hacked up. Perhaps it will be useful to you too!

