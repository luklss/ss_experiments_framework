select 
  expnames.experimenttypename,
  expmodes.experimentmodename,
  ed.experimentmodeid,
  fd.isdesktop,
  ck.culturekey,
  date_trunc('day', c.creationdate) as theday,
  -- get the device
  -- get if completed checkout
  case 
  when exists (
    select * from tblUserEventLog uel where uel.customerid=c.customerid and uel.usereventtype=17 and uel.usereventtimeframe = 0
  )
  then 1
  else 0
  end as completedcheckout30m,
  -- get if is qp6h
  case 
  when exists (
  select grc.customerid, grc.qp6h from grepconversion grc where c.customerid = grc.customerid and grc.qp6h = 1
  )
  then 1
  else 0
  end as qp6h,
  -- get sco30m
  case
  when exists (
  select * from tblUserEventLog uel where uel.customerid=c.customerid and uel.usereventtype=5 and usereventtimeframe = 0
  )
  then 1
  else 0
  end as sco30m,
  -- in this data model, everyone is a trial :)
  1 as trial
from tblCustomers c (nolock)
inner join gdeffirstdevice fd on fd.customerid = c.customerid
inner join gdefculturekey ck (nolock) on ck.customerid=c.customerid
inner join tblexperimentdata ed (nolock) on ed.customerid=c.customerid
inner join tblexperimenttypes expnames on ed.experimenttypeid = expnames.experimenttypeid
inner join tblexperimentmodes expmodes on ed.experimenttypeid = expmodes.experimenttypeid and ed.experimentmodeid = expmodes.experimentmodeid
