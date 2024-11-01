from libdebug import debugger
import liballocate
import IPython

d = debugger("/bin/ls")

d.run()

liballocate.activate(d)

IPython.embed()

