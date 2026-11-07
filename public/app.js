const $=(s,root=document)=>root.querySelector(s);
const $$=(s,root=document)=>[...root.querySelectorAll(s)];
const root=$('#root'), modals=$('#modal-root'), toastRoot=$('#toast-root');
const state={me:null,view:'dashboard',page:1,search:'',menu:false,notifOpen:false,lookups:{},data:{},report:'sales',busy:false};
const fa=(num)=>new Intl.NumberFormat('fa-IR').format(Number(num)||0);
const money=(num)=>`${fa(num)} تومان`;
const dateFa=(val)=>{try{return new Intl.DateTimeFormat('fa-IR-u-ca-persian',{year:'numeric',month:'short',day:'numeric'}).format(new Date(val))}catch{return '—'}};
const esc=(s)=>String(s??'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
const uid=()=>crypto.randomUUID?.()||Math.random().toString(36).slice(2);
const ICON={grid:'<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>',box:'<path d="m12 2 9 5-9 5-9-5 9-5Z"/><path d="M3 7v10l9 5 9-5V7M12 12v10"/>',layers:'<path d="m12 2 9 5-9 5-9-5 9-5ZM3 12l9 5 9-5M3 17l9 5 9-5"/>',warehouse:'<path d="m3 10 9-7 9 7v11H3V10ZM9 21v-8h6v8"/>',swap:'<path d="M4 7h16l-4-4m4 4-4 4M20 17H4l4-4m-4 4 4 4"/>',cart:'<circle cx="9" cy="21" r="1"/><circle cx="19" cy="21" r="1"/><path d="M1 1h4l3 15h12l2-11H6"/>',users:'<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2M16 3.1a4 4 0 0 1 0 7.8M22 21v-2a4 4 0 0 0-3-3.9"/><circle cx="9" cy="7" r="4"/>',truck:'<path d="M1 5h13v13H1zM14 9h4l4 4v5h-8"/><circle cx="6" cy="19" r="2"/><circle cx="18" cy="19" r="2"/>',card:'<rect x="2" y="4" width="20" height="16" rx="2"/><path d="M2 10h20"/>',chart:'<path d="M3 3v18h18M7 16l4-5 4 3 5-8"/>',settings:'<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06-2 2-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-.95 1.51V21h-3v-.09A1.65 1.65 0 0 0 10.35 19a1.65 1.65 0 0 0-1.82.33l-.06.06-2-2 .06-.06A1.65 1.65 0 0 0 6.86 15a1.65 1.65 0 0 0-1.51-.95H5v-3h.35A1.65 1.65 0 0 0 6.86 10a1.65 1.65 0 0 0-.33-1.82l-.06-.06 2-2 .06.06A1.65 1.65 0 0 0 10.35 6 1.65 1.65 0 0 0 11 4.5V4h3v.5A1.65 1.65 0 0 0 15.35 6a1.65 1.65 0 0 0 1.82-.33l.06-.06 2 2-.06.06A1.65 1.65 0 0 0 19.4 10 1.65 1.65 0 0 0 21 11h.5v3H21a1.65 1.65 0 0 0-1.6 1Z"/>',bell:'<path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4"/>',search:'<circle cx="10" cy="10" r="7"/><path d="m15 15 6 6"/>',plus:'<path d="M12 5v14M5 12h14"/>',edit:'<path d="M12 20h9M3 17.2V21h3.8L19.8 8l-3.8-3.8L3 17.2Z"/>',trash:'<path d="M3 6h18M8 6V4h8v2M6 6l1 15h10l1-15M10 11v6M14 11v6"/>',check:'<path d="m5 12 4 4L19 6"/>',x:'<path d="m5 5 14 14M19 5 5 19"/>',menu:'<path d="M4 7h16M4 12h16M4 17h16"/>',logout:'<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9"/>',download:'<path d="M12 3v13m-5-5 5 5 5-5M3 20h18"/>',calendar:'<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M8 3v4M16 3v4M3 10h18"/>',coins:'<circle cx="12" cy="12" r="9"/><path d="M12 6v12M16 9H9a2 2 0 0 0 0 4h6a2 2 0 0 1 0 4H8"/>',returns:'<path d="M9 14 4 9l5-5M4 9h10a6 6 0 0 1 0 12h-2"/>',help:'<circle cx="12" cy="12" r="10"/><path d="M9.5 9a2.5 2.5 0 1 1 4.5 1.5c-1 1-2 1.5-2 3.5M12 17h.01"/>',file:'<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Zm0 0v6h6M8 13h8M8 17h8"/>',clock:'<circle cx="12" cy="12" r="9"/><path d="M12 7v5l4 2"/>',tag:'<path d="M20 13 13 20a2 2 0 0 1-3 0l-8-8V3h9l9 8a2 2 0 0 1 0 2Z"/><circle cx="7" cy="8" r="1"/>'};
function icon(name,size=18){return `<span class="icon"><svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICON[name]||ICON.box}</svg></span>`}
const NAV=[
 ['نمای کلی',[['dashboard','داشبورد','grid'],['notifications','اعلان‌ها','bell']]],
 ['کالا و موجودی',[['products','کالاها','box'],['variants','تنوع و قیمت','layers'],['categories','دسته‌بندی‌ها','tag'],['warehouses','انبارها','warehouse'],['stocks','موجودی کالا','box'],['batches','بچ و تاریخ انقضا','layers'],['serials','شماره سریال‌ها','tag'],['lot-movements','گردش بچ‌ها','layers'],['expiry-alerts','هشدار انقضا','bell'],['movements','گردش انبار','swap'],['cycle-count','انبارگردانی','check'],['transfers','انتقال بین انبارها','swap']]],
 ['خرید و فروش',[['suppliers','تأمین‌کنندگان','truck'],['purchases','سفارش‌های خرید','cart'],['customers','مشتریان','users'],['sales','فروش و سفارش‌ها','cart'],['fulfillments','ارسال‌های جزئی','truck'],['returns','مرجوعی‌ها','returns'],['shipments','ارسال و رهگیری','truck']]],
 ['امور مالی',[['invoices','فاکتورهای فروش','file'],['payments','پرداخت‌ها','coins'],['cash-accounts','حساب‌ها','card'],['ledger-accounts','کدینگ حسابداری','layers'],['ledger-journals','اسناد حسابداری','file'],['ledger-balance','تراز آزمایشی','chart'],['ledger-profit','سود و زیان','chart'],['account-entries','گردش حساب‌ها','file'],['price-lists','لیست‌های قیمت','tag'],['price-items','قیمت‌های اختصاصی','tag'],['tax-rates','مالیات‌ها','file'],['reports','گزارش‌ها','chart'],['analytics','تحلیل پیشرفته','chart']]],
 ['مدیریت',[['team','کاربران و دسترسی','users'],['settings','تنظیمات کسب‌وکار','settings'],['security','امنیت و نشست‌ها','settings'],['integrations','اتصالات آینده','settings'],['audit','تاریخچه عملیات','clock']]]
];
const LABELS={id:'شناسه',name:'نام',sku:'کد کالا',code:'کد انبار',barcode:'بارکد',unit:'واحد',description:'توضیحات',category_id:'دسته‌بندی',product_id:'کالا',warehouse_id:'انبار',variant_id:'تنوع کالا',supplier_id:'تأمین‌کننده',customer_id:'مشتری',group_name:'گروه',price:'قیمت',purchase_cost:'بهای خرید',retail_price:'قیمت فروش',wholesale_price:'قیمت عمده',low_stock:'حد هشدار',quantity:'تعداد',reserved:'رزروشده',delta:'تغییر',number:'شماره',status:'وضعیت',total:'مبلغ کل',paid:'پرداخت‌شده',discount:'تخفیف',channel:'کانال فروش',phone:'تلفن',email:'ایمیل',address:'نشانی',notes:'توضیحات',active:'فعال',archived:'آرشیو',read:'خوانده شده',amount:'مبلغ',method:'روش',reference_id:'مرجع',created_at:'تاریخ',carrier:'شرکت حمل',tracking_number:'کد رهگیری',role:'نقش',opening_balance:'موجودی اولیه',percentage:'درصد',title:'عنوان',body:'متن',category:'نوع',reason:'علت',source_id:'انبار مبدأ',destination_id:'انبار مقصد',direction:'جهت',restock:'بازگشت به موجودی',expiry_date:'تاریخ انقضا',lot:'سری ساخت',order_id:'سفارش',purchase_id:'خرید',list_id:'لیست قیمت',actor_id:'کاربر',entity:'موجودیت',action:'عملیات',credit_limit:'سقف اعتبار',track_batch:'ردیابی بچ',track_serial:'ردیابی سریال',image_url:'آدرس تصویر'};
const NUMERIC=new Set(['purchase_cost','retail_price','wholesale_price','low_stock','credit_limit','price','opening_balance','percentage','quantity','delta','discount']);
const MONETARY=new Set(['purchase_cost','retail_price','wholesale_price','credit_limit','price','opening_balance','total','paid','discount','amount']);
const BOOLEAN=new Set(['active','track_batch','track_serial','restock']);
const REF={category_id:'categories',product_id:'products',warehouse_id:'warehouses',variant_id:'variants',supplier_id:'suppliers',customer_id:'customers',order_id:'sales',list_id:'price-lists'};
const META={
 categories:{cols:['name','created_at'],fields:['name','parent_id']},
 products:{cols:['name','category_id','active','created_at'],fields:['name','category_id','description','image_url','active']},
 variants:{cols:['sku','name','purchase_cost','retail_price','low_stock','active'],fields:['product_id','name','sku','barcode','unit','purchase_cost','retail_price','wholesale_price','low_stock','track_batch','track_serial','active']},
 warehouses:{cols:['name','code','address','active'],fields:['name','code','address','active']},
 stocks:{cols:['variant_id','warehouse_id','quantity','reserved'],readonly:true},
 batches:{cols:['variant_id','warehouse_id','lot','expiry_date','quantity'],readonly:true},
 serials:{cols:['serial','variant_id','warehouse_id','status','reference_id'],readonly:true},
 'lot-movements':{cols:['variant_id','warehouse_id','batch_id','delta','reason','created_at'],readonly:true},
 movements:{cols:['variant_id','warehouse_id','delta','reason','created_at'],readonly:true},
 transfers:{cols:['variant_id','quantity','source_id','destination_id','status'],special:'transfer'},
 suppliers:{cols:['name','phone','email','created_at'],fields:['name','phone','email','address','notes']},
 purchases:{cols:['number','supplier_id','status','total','paid','created_at'],special:'purchase'},
 customers:{cols:['name','phone','group_name','credit_limit','created_at'],fields:['name','phone','email','address','group_name','credit_limit']},
 sales:{cols:['number','customer_id','status','total','paid','created_at'],special:'sale'},
 returns:{cols:['direction','variant_id','quantity','amount','created_at'],readonly:true},
 shipments:{cols:['order_id','carrier','tracking_number','status'],fields:['order_id','carrier','tracking_number','status','address']},
 payments:{cols:['order_id','purchase_id','amount','method','created_at'],readonly:true},
 'cash-accounts':{cols:['name','type','opening_balance'],fields:['name','type','opening_balance']},
 'account-entries':{cols:['account_id','direction','amount','created_at'],readonly:true},
 'price-lists':{cols:['name','group_name','active'],fields:['name','group_name','active']},
 'price-items':{cols:['list_id','variant_id','price'],fields:['list_id','variant_id','price']},
 'tax-rates':{cols:['name','percentage'],fields:['name','percentage']},
 notifications:{cols:['title','body','category','read','created_at'],readonly:true},
 audit:{cols:['action','entity','entity_id','created_at'],readonly:true}
};
const titleOf=key=>NAV.flatMap(group=>group[1]).find(x=>x[0]===key)?.[1]||'داشبورد';
const CREATE_LABEL={products:'کالای جدید',variants:'تنوع جدید',categories:'دسته‌بندی جدید',warehouses:'انبار جدید',suppliers:'تأمین‌کننده جدید',customers:'مشتری جدید',shipments:'ارسال جدید','cash-accounts':'حساب جدید','price-lists':'لیست قیمت جدید','price-items':'قیمت اختصاصی جدید','tax-rates':'مالیات جدید'};
const roleCan=(name)=>{
 if(state.me?.public_demo)return false;
 const p=state.me?.role;
 if(['owner','admin'].includes(p))return true;
 if(['products','variants','categories','warehouses','stocks','transfers'].includes(name))return p==='inventory_manager';
 if(['customers','sales','shipments','price-lists','price-items'].includes(name))return p==='sales';
 if(['purchases','suppliers'].includes(name))return ['inventory_manager','accountant'].includes(p);
 if(['cash-accounts','tax-rates'].includes(name))return p==='accountant';
 return false;
};
const notify=(txt,error=false)=>{const n=document.createElement('div');n.className='toast'+(error?' error':'');n.textContent=txt;toastRoot.append(n);setTimeout(()=>n.remove(),4200)};
async function api(path,{method='GET',body}={}){
 let result;
 try{result=await fetch('/api/'+path,{method,headers:{...(body!==undefined?{'Content-Type':'application/json'}:{})},credentials:'same-origin',body:body!==undefined?JSON.stringify(body):undefined})}
 catch(e){throw Error('ارتباط با سرور برقرار نشد')}
 let data;try{data=await result.json()}catch{data={detail:'پاسخ نامعتبر سرور'}}
 if(!result.ok){if(result.status===401&&state.me){state.me=null;renderAuth()}throw Error(typeof data.detail==='string'?data.detail:'خطایی در درخواست رخ داد')}
 return data;
}
async function lookup(resource,reload=false){if(!state.lookups[resource]||reload){const r=await api(`data/${resource}?limit=100`);state.lookups[resource]=r.items||[]}return state.lookups[resource]}
function status(v){const text={draft:'پیش‌نویس',confirmed:'تأیید شده',fulfilled:'تحویل‌شده',cancelled:'لغوشده',received:'دریافت‌شده',partial:'دریافت ناقص',shipped:'ارسال‌شده',delivered:'تحویل‌شده',pending:'در انتظار',retail:'خرده‌فروشی',wholesale:'عمده',online:'آنلاین',pos:'حضوری',cash:'نقدی',card:'کارت',transfer:'انتقال',sale:'برگشت فروش',purchase:'برگشت خرید',in:'واریز',out:'برداشت'};
 const mood=['fulfilled','received','delivered'].includes(v)?'good':['cancelled','returned'].includes(v)?'bad':['draft','partial','pending','confirmed','shipped'].includes(v)?'warn':'';
 return `<span class="pill ${mood}">${esc(text[v]||v||'—')}</span>`;
}
function val(k,v){if(v===null||v===undefined||v==='')return '<span class="muted">—</span>';if(k==='created_at'||k==='expiry_date')return dateFa(v);if(k==='status'||k==='channel'||k==='direction'||k==='method')return status(v);if(typeof v==='boolean')return v?'<span class="pill good">بله</span>':'<span class="pill">خیر</span>';if(MONETARY.has(k))return `<span class="num">${money(v)}</span>`;if(NUMERIC.has(k))return fa(v);if(k.endsWith('_id'))return `<span title="${esc(v)}">${esc(String(v).slice(0,8))}…</span>`;return esc(v)}
function renderAuth(mode='login'){
 state.me=null;clearInterval(window.__erpPoll);window.__erpPoll=null;
 const register=mode==='register';
 root.innerHTML=`<div class="auth-layout"><div class="auth-aside"><div class="hero"><div class="auth-logo"><span class="logo-symbol">◈</span> ERP فروشگاهی</div><h1>تمام کسب‌وکارت<br>در یک پنل منظم.</h1><p>فروش، خرید، انبار و گزارش‌های مالی را در یک محیط هماهنگ مدیریت کنید. دقیق، سریع و متناسب با فروشگاه‌های ایرانی.</p></div></div><div class="auth-form-area"><div class="auth-form"><div class="auth-logo" style="color:var(--primary)"><span class="logo-symbol" style="background:#e9f0ff">◈</span> ERP فروشگاهی</div><h2>${register?'ایجاد حساب کسب‌وکار':'ورود به پنل مدیریت'}</h2><p class="subtitle">${register?'با ساخت حساب، فضای اختصاصی فروشگاه شما ایجاد می‌شود.':'برای ادامه، اطلاعات ورود خود را وارد کنید.'}</p><div class="segmented"><button type="button" class="${!register?'active':''}" data-auth-tab="login">ورود به حساب</button><button type="button" class="${register?'active':''}" data-auth-tab="register">ثبت‌نام</button></div><form id="auth-form" data-mode="${mode}">${register?`<div class="field"><label>نام و نام خانوادگی</label><input class="input" name="name" required maxlength="120" autocomplete="name" placeholder="نام شما"></div><div class="field"><label>نام کسب‌وکار</label><input class="input" name="company" required maxlength="200" placeholder="مثلاً فروشگاه آسمان"></div>`:''}<div class="field"><label>ایمیل</label><input class="input" name="email" type="email" required autocomplete="email" placeholder="name@example.com" dir="ltr"></div><div class="field"><label>رمز عبور</label><input class="input" name="password" type="password" required minlength="${register?'12':'1'}" autocomplete="${register?'new-password':'current-password'}" placeholder="${register?'حداقل ۱۲ نویسه':'رمز عبور'}" dir="ltr"></div>${register?`<div class="notice">با ثبت‌نام، یک سازمان، انبار اصلی و صندوق اولیه به‌صورت خودکار ساخته می‌شود. تمام اطلاعات فقط به فضای شما متعلق است.</div>`:''}<button class="btn btn-primary" type="submit">${register?'ساخت حساب +':'ورود به پنل'}</button></form><p class="auth-note">اطلاعات هر فروشگاه به‌صورت مجزا ذخیره می‌شوند. برای امنیت بیشتر از رمز عبور طولانی و اختصاصی استفاده کنید.</p></div></div></div>`;
}
function renderShell(){
 const nav=NAV.map(([group,items])=>`<div class="nav-caption">${esc(group)}</div>${items.map(([key,name,ic])=>`<button class="nav-btn ${state.view===key?'active':''}" data-nav="${key}" type="button">${icon(ic)}<span>${esc(name)}</span></button>`).join('')}`).join('');
 root.innerHTML=`<div class="shell" id="shell"><aside class="sidebar"><div class="side-head"><span class="logo-symbol" style="background:#ecf2ff">◈</span><div><h1>ERP فروشگاهی</h1><p>پنل یکپارچه کسب‌وکار</p></div></div><div class="side-scroll">${nav}</div><div class="side-footer"><div class="org-card row"><span class="avatar">${esc(state.me.tenant.slice(0,1))}</span><div class="spacer truncate"><div class="org-name truncate">${esc(state.me.tenant)}</div><div class="org-role">${state.me.public_demo?'دموی عمومی · فقط مشاهده':esc(state.me.role)}</div></div><button class="btn btn-small" data-nav="settings" title="تنظیمات">${icon('settings')}</button></div>${state.me.public_demo?'<div class="hint" style="padding:10px 0;text-align:center">داده‌ها نمونه و غیرواقعی هستند</div>':`<button class="btn btn-small" id="logout" style="width:100%;margin-top:9px;color:var(--muted);justify-content:flex-start">${icon('logout')} خروج از حساب</button>`}</div></aside><div class="menu-shade" id="menu-shade"></div><main class="main"><header class="topbar"><div class="row"><button class="top-icon menu-toggle" id="menu-toggle" aria-label="باز کردن منو">${icon('menu')}</button><div><h2 class="top-title" id="top-title">${esc(titleOf(state.view))}</h2><div class="top-subtitle">${esc(state.me.tenant)} / پنل مدیریت</div></div></div><div class="top-actions"><div style="position:relative"><button class="top-icon" id="notif-toggle" aria-label="اعلان‌ها">${icon('bell')}<span class="dot hide" id="notif-dot"></span></button><div id="notif-pop" class="pop hide"></div></div><span class="user-avatar" title="${esc(state.me.name)}">${esc(state.me.name.slice(0,1))}</span></div></header>${state.me.public_demo?`<div class="notice" style="margin:16px 22px 0;border-radius:12px;padding:12px 16px"><strong>پیش‌نمایش عمومی ERP</strong> — داده‌های دمو در تمام بخش‌ها قرار دارند. ثبت و ویرایش در این نمایش غیرفعال است؛ اطلاعات واقعی سایر کسب‌وکارها محفوظ می‌ماند.</div>`:''}<section class="content" id="page-content"><div class="boot" style="min-height:250px"><span class="loader"></span></div></section></main></div>`;
 if(!window.__erpPoll)window.__erpPoll=setInterval(refreshNotifs,12000);
 refreshNotifs();
}
async function refreshNotifs(){if(!state.me)return;try{
 const r=await api('data/notifications?limit=8');
 const unread=r.items.filter(x=>!x.read);
 $('#notif-dot')?.classList.toggle('hide',unread.length===0);
 const pop=$('#notif-pop');if(pop){pop.innerHTML=`<div class="between"><strong>اعلان‌های اخیر</strong><button class="btn btn-small btn-light" data-nav="notifications">مشاهده همه</button></div>${r.items.length?r.items.map(x=>`<div class="recent-item"><div class="between"><span class="strong">${esc(x.title)}</span>${x.read||state.me?.public_demo?'':`<button class="btn btn-small btn-light" data-mark-read="${x.id}">${icon('check')} خواندم</button>`}</div><div class="muted" style="margin-top:5px">${esc(x.body||'')}</div><div class="hint">${dateFa(x.created_at)}</div></div>`).join(''):'<div class="empty" style="padding:23px">اعلان جدیدی وجود ندارد</div>'}`}
 }catch{ /* Background polling is best-effort; foreground API errors remain visible. */ }}
function setView(key){
 state.view=key;state.page=1;state.search='';state.menu=false;state.notifOpen=false;
 $('#shell')?.classList.remove('menu-open');$('#notif-pop')?.classList.add('hide');
 $$('.nav-btn').forEach(b=>b.classList.toggle('active',b.dataset.nav===key));
 const top=$('#top-title');if(top)top.textContent=titleOf(key);
 history.replaceState(null,'','#'+key);
 loadView();
}
function head(title,sub='',button=''){
 return `<div class="page-head"><div><h2>${esc(title)}</h2><p>${esc(sub)}</p></div>${button}</div>`;
}
async function loadView(){
 const main=$('#page-content');if(!main)return;
 main.innerHTML='<div class="boot" style="min-height:250px"><span class="loader"></span><span>در حال دریافت اطلاعات...</span></div>';
 try{
   if(state.view==='dashboard')await renderDashboard();
   else if(state.view==='invoices')await renderInvoices();
   else if(state.view==='fulfillments')await renderFulfillments();
   else if(state.view==='reports')await renderReports();
   else if(state.view==='analytics')await renderAnalytics();
   else if(state.view==='expiry-alerts')await renderExpiryAlerts();
   else if(state.view==='integrations')await renderIntegrations();
   else if(state.view==='security')await renderSecurity();
   else if(state.view.startsWith('ledger-'))await renderLedger();
   else if(state.view==='cycle-count')await renderCycleCount();
   else if(state.view==='settings')await renderSettings();
   else if(state.view==='team')await renderTeam();
   else if(META[state.view])await renderResource();
   else setView('dashboard');
 }catch(e){main.innerHTML=`${head(titleOf(state.view))}<div class="panel empty">${icon('help',30)}<strong>دریافت اطلاعات انجام نشد</strong><p>${esc(e.message)}</p><button class="btn btn-primary" id="retry-view">تلاش دوباره</button></div>`}
}
async function renderDashboard(){
 const [d,sales]=await Promise.all([api('dashboard'),api('data/sales?limit=100')]);
 const cards=[['فروش ثبت‌شده',d.sales,'coins',true],['مبالغ دریافت‌شده',d.sales_paid,'card',true],['سفارش‌های فروش',d.orders,'cart'],['ارزش موجودی',d.stock_value,'warehouse',true],['اقلام موجود در انبار',d.stock_count,'box'],['مطالبات از مشتریان',d.receivables,'file',true],['هزینه خرید',d.purchase,'truck',true],['کالاهای کم‌موجود',d.low_stock,'bell']];
 const days=[];for(let i=6;i>=0;i--){const dt=new Date();dt.setHours(0,0,0,0);dt.setDate(dt.getDate()-i);days.push({date:dt,y:0,caption:new Intl.DateTimeFormat('fa-IR',{weekday:'short'}).format(dt)})}
 sales.items.forEach(o=>{if(o.status==='cancelled')return;const when=new Date(o.created_at);for(let i=0;i<days.length;i++){if(when>=days[i].date && (!days[i+1]||when<days[i+1].date)){days[i].y+=o.total;break}}});
 const max=Math.max(...days.map(x=>x.y),1);
 $('#page-content').innerHTML=`${head('نمای کلی فروشگاه','تصویری سریع از وضعیت مالی، موجودی و سفارش‌های شما')}
 <div class="metric-grid">${cards.map(([title,number,ic,isMoney])=>`<div class="panel metric-card"><div class="label"><span>${title}</span><span class="metric-icon">${icon(ic)}</span></div><strong class="num">${isMoney?fa(number):fa(number)}</strong><small>${isMoney?'تومان':'مورد'}</small></div>`).join('')}</div>
 <div class="dashboard-layout"><div class="panel panel-padded"><div class="between"><div><div class="panel-title">فروش هفت روز اخیر</div><div class="panel-sub">بر اساس سفارش‌های ثبت‌شده، بدون احتساب سفارش‌های لغوشده</div></div>${icon('chart',23)}</div><div class="bars">${days.map(d=>`<div class="bar-item" title="${money(d.y)}"><div class="bar" style="height:${Math.max(2,d.y/max*90)}%"></div><span class="bar-label">${esc(d.caption)}</span></div>`).join('')}</div><div class="hint">اعداد نمودار از اطلاعات واقعی سفارش‌ها محاسبه می‌شوند.</div></div><div class="panel panel-padded"><div class="between"><div><div class="panel-title">آخرین فعالیت‌ها</div><div class="panel-sub">اعلان‌ها و وضعیت سفارش‌ها</div></div><button class="btn btn-small btn-light" data-nav="notifications">همه</button></div>${d.notifications.length?d.notifications.slice(0,5).map(x=>`<div class="recent-item row">${icon('bell')}<div><div class="strong">${esc(x.title)}</div><div class="muted">${esc(x.body||'')}</div></div></div>`).join(''):'<div class="empty">هنوز فعالیتی ثبت نشده است.</div>'}</div></div>`;
}
function actionBtns(resource,item){
 const allowed=roleCan(resource);let out='';
 if(META[resource]?.fields && allowed){out+=`<button class="btn btn-small btn-light" data-edit="${esc(resource)}:${esc(item.id)}">ویرایش ${icon('edit',14)}</button><button class="btn btn-small btn-danger" data-delete="${esc(resource)}:${esc(item.id)}">حذف ${icon('trash',14)}</button>`}
 if(allowed && resource==='transfers'){
  const act={draft:['ship','ارسال'],shipped:['receive','دریافت']}[item.status];if(act)out+=`<button class="btn btn-small btn-primary" data-workflow="transfers:${item.id}:${act[0]}">${act[1]} ${icon('check',14)}</button>`;
 }
 if(state.me?.public_demo&&['purchases','sales','returns','transfers','shipments','stocks','payments'].includes(resource)){
  out+=`<button class="btn btn-small btn-outline" type="button" data-demo-workflow="${esc(resource)}">نمایش امکانات ${icon('file',14)}</button>`;
 }
 if(allowed && resource==='purchases'){
   if(!['received','cancelled'].includes(item.status))out+=`<button class="btn btn-small btn-primary" data-workflow="purchases:${item.id}:receive">دریافت کالا ${icon('check',14)}</button>`;
   if(['received','partial'].includes(item.status))out+=`<button class="btn btn-small btn-light" data-document-action="purchase-return:${item.id}">مرجوعی ${icon('returns',14)}</button>`;
   if(roleCan('cash-accounts')&&item.paid<item.total)out+=`<button class="btn btn-small btn-light" data-document-action="pay-purchase:${item.id}">پرداخت ${icon('coins',14)}</button>`;
 }
 if(allowed && resource==='sales'){
   const statuses={draft:[['confirm','تأیید'],['cancel','لغو']],confirmed:[['fulfill','تحویل کامل'],['cancel','لغو']],partial:[['fulfill','ارسال مانده']]};
   (statuses[item.status]||[]).forEach(([act,t])=>out+=`<button class="btn btn-small ${act==='cancel'?'btn-danger':'btn-primary'}" data-workflow="sales:${item.id}:${act}">${t} ${icon(act==='cancel'?'x':'check',14)}</button>`);
   if(['confirmed','partial'].includes(item.status))out+=`<button class="btn btn-small btn-outline" data-partial-fulfill="${esc(item.id)}">ارسال جزئی ${icon('truck',14)}</button>`;
   if(['fulfilled','partial'].includes(item.status))out+=`<button class="btn btn-small btn-light" data-document-action="sale-return:${item.id}">مرجوعی ${icon('returns',14)}</button>`;
   if(item.status!=='cancelled'&&item.paid<item.total)out+=`<button class="btn btn-small btn-light" data-document-action="pay-sale:${item.id}">پرداخت ${icon('coins',14)}</button>`;
 }
 if(resource==='returns'&&roleCan('cash-accounts'))
   out+=`<button class="btn btn-small btn-light" data-return-settle="${esc(item.id)}">تسویه وجه ${icon('coins',14)}</button>`;
 if(resource==='notifications'&&!item.read&&!state.me?.public_demo)out+=`<button class="btn btn-small btn-light" data-mark-read="${item.id}">خواندم ${icon('check',14)}</button>`;
 return out;
}
async function renderCycleCount(selectedWarehouse){
 const warehouses=await lookup('warehouses',true);
 const main=$('#page-content');
 if(!warehouses.length){
  main.innerHTML=head('انبارگردانی','ابتدا یک انبار بسازید')+'<div class="panel panel-padded"><p>برای شروع انبارگردانی، یک انبار ثبت کنید.</p></div>';
  return;
 }
 const warehouse_id=selectedWarehouse||$('#cycle-warehouse')?.value||warehouses[0].id;
 const result=await api('stock/cycle-sheet?warehouse_id='+encodeURIComponent(warehouse_id)+'&page='+state.page);
 const rows=result.items.map(item=>`<tr class="count-row" data-variant="${esc(item.variant_id)}" data-expected="${item.quantity}">
 <td><strong>${esc(item.sku)}</strong><div class="muted">${esc(item.name)}</div></td>
 <td class="num">${fa(item.quantity)}</td><td class="num">${fa(item.reserved)}</td>
 <td style="min-width:130px"><input type="number" name="counted" class="input" ${state.me?.public_demo?'readonly':''} required min="${item.reserved}" step="1" max="1000000" value="${item.quantity}" aria-label="تعداد شمارش‌شده ${esc(item.sku)}"></td></tr>`).join('');
 const options=warehouses.map(w=>`<option value="${esc(w.id)}" ${w.id===warehouse_id?'selected':''}>${esc(w.name)}</option>`).join('');
 main.innerHTML=`${head('انبارگردانی','موجودی واقعی را وارد کنید. اگر در این فاصله موجودی تغییر کند، ثبت متوقف می‌شود.')}
 <div class="panel panel-padded" style="margin-bottom:18px"><div class="row wrap between"><div class="field" style="min-width:220px"><label>انبار مورد شمارش</label><select class="input" id="cycle-warehouse">${options}</select></div><button type="button" class="btn btn-outline" id="count-refresh">دریافت موجودی تازه ${icon('swap',16)}</button></div>
 <p class="notice">موجودی رزروشده قابل کاهش نیست. هر صفحه تا ۱۰۰ کالا دارد. اختلاف‌ها در گردش انبار و تاریخچه عملیات ثبت می‌شوند.</p></div>
 <form id="cycle-count-form"><div class="panel"><div class="table-wrap"><table class="table">
 <thead><tr><th>کالا</th><th>موجودی سیستم</th><th>رزروشده</th><th>شمارش واقعی</th></tr></thead>
 <tbody>${rows||'<tr><td colspan="4" class="muted">کالای فعالی وجود ندارد</td></tr>'}</tbody></table></div>
 <div class="pagination"><span>صفحه ${fa(state.page)} از ${fa(Math.max(1,Math.ceil(result.total/100)))}</span>
 <div class="row"><button type="button" class="btn btn-small btn-outline" id="count-prev" ${state.page<=1?'disabled':''}>قبلی</button>
 <button type="button" class="btn btn-small btn-outline" id="count-next" ${state.page*100>=result.total?'disabled':''}>بعدی</button></div></div></div>
 ${state.me?.public_demo?'':`<div class="row" style="margin-top:16px"><button class="btn btn-primary" id="cycle-submit" type="submit" ${!result.items.length?'disabled':''}>ثبت انبارگردانی ${icon('check',16)}</button></div>`}</form>`;
}

function openDemoWorkflow(resource){
 const details={
   sales:['ثبت سفارش با چند قلم کالا، تخفیف و کانال فروش','تأیید سفارش و کنترل موجودی رزروشده','تحویل کامل یا جزئی و ثبت گردش انبار','ثبت دریافت وجه، صدور فاکتور و مرجوعی'],
   purchases:['ثبت سفارش تأمین‌کننده با چند کالا','دریافت کامل یا چندمرحله‌ای و ثبت خودکار موجودی','تسویه تأمین‌کننده و ثبت مرجوعی خرید'],
   transfers:['انتخاب انبار مبدأ و مقصد و کالا','ارسال انتقال با ثبت خروج موجودی','ثبت دریافت در مقصد و دفتر گردش'],
   returns:['برگشت کالاهای فروش یا خرید','تصمیم‌گیری درباره بازگشت به موجودی','تسویه وجه همراه با ثبت مالی و حسابرسی'],
   shipments:['انتخاب سفارش، حمل‌کننده و شماره رهگیری','ثبت وضعیت ارسال، تحویل یا برگشت','مشاهده سوابق ارسال‌های کامل و جزئی'],
   stocks:['اصلاح موجودی با دلیل و ثبت سند گردش','شمارش انبار و جلوگیری از اختلاف هم‌زمان','ردیابی بچ، تاریخ انقضا و شماره سریال'],
   payments:['ثبت دستی دریافت یا پرداخت روی سفارش','انتساب حساب بانکی یا صندوق','کنترل تراکنش تکراری و تطبیق مبلغ'],
 };
 const rows=details[resource]||['گردش کاری این ماژول بر اساس داده واقعی انجام می‌شود'];
 const html='<div class="notice">این پنجره قابلیت‌های این ماژول را توضیح می‌دهد. در دموی عمومی عملیات واقعی عمداً غیرفعال است.</div><ol style="padding-inline-start:24px;line-height:2.3">'+
   rows.map(x=>'<li>'+esc(x)+'</li>').join('')+'</ol>';
 showModal('قابلیت‌های '+titleOf(resource),html,null,{save:'متوجه شدم'});
}

async function renderResource(){
 const resource=state.view,meta=META[resource];
 const url=`data/${resource}?page=${state.page}&limit=25&search=${encodeURIComponent(state.search)}`;
 const result=await api(url);state.data[resource]=result.items;
 const btn=(state.me?.public_demo&&!meta.readonly)?
   `<button class="btn btn-primary" id="new-record">مشاهده فرم ${icon('file',17)}</button>`:
   (resource==='stocks'&&roleCan('stocks'))?`<button class="btn btn-outline" id="register-serials">ثبت سریال ${icon('plus',16)}</button><button class="btn btn-primary" id="adjust-stock">اصلاح موجودی ${icon('plus',17)}</button>`:(!meta.readonly&&roleCan(resource))?`<button class="btn btn-primary" id="new-record">${meta.special==='sale'?'سفارش جدید':meta.special==='purchase'?'سفارش خرید جدید':meta.special==='transfer'?'انتقال جدید':(CREATE_LABEL[resource]||titleOf(resource)+' جدید')} ${icon('plus',17)}</button>`:'';
 const csvLink=`<a class="btn btn-outline" href="/api/export/${encodeURIComponent(resource)}.csv" target="_blank" rel="noopener noreferrer">خروجی CSV ${icon('download',15)}</a>`;
 const headHtml=head(titleOf(resource),`مشاهده و مدیریت اطلاعات ${titleOf(resource)} در سازمان شما`,csvLink+btn);
 const cols=[...meta.cols];const rows=result.items.map(item=>{
  const values=cols.map(k=>`<td>${val(k,item[k])}</td>`).join('');
  const actions=actionBtns(resource,item);
  return `<tr>${values}${actions?`<td><div class="actions">${actions}</div></td>`:''}</tr>`;
 }).join('');
 const hasActions=result.items.some(item=>actionBtns(resource,item));
 const mobiles=result.items.map(item=>`<div class="mobile-card"><div class="between"><strong>${esc(item.name||item.number||item.sku||item.title||item.code||String(item.id).slice(0,10))}</strong>${item.status?status(item.status):''}</div><div class="mobile-fields">${cols.filter(k=>k!=='status').slice(0,6).map(k=>`<div><label>${esc(LABELS[k]||k)}</label><div class="value">${val(k,item[k])}</div></div>`).join('')}</div>${actionBtns(resource,item)?`<div class="row wrap">${actionBtns(resource,item)}</div>`:''}</div>`).join('');
 $('#page-content').innerHTML=`${headHtml}<div class="panel"><div class="table-toolbar"><div class="search-box"><input class="input" id="table-search" placeholder="جست‌وجو در ${esc(titleOf(resource))}..." value="${esc(state.search)}" autocomplete="off"/></div><span class="muted">${fa(result.total)} رکورد</span></div>${result.items.length?`<div class="table-wrap"><table class="table"><thead><tr>${cols.map(k=>`<th>${esc(LABELS[k]||k)}</th>`).join('')}${hasActions?'<th>عملیات</th>':''}</tr></thead><tbody>${rows}</tbody></table></div><div class="mobile-cards">${mobiles}</div>`:`<div class="empty">${icon('box',28)}<strong>موردی ثبت نشده است</strong><span>برای شروع از گزینه ایجاد استفاده کنید.</span></div>`}<div class="pagination"><span>صفحه ${fa(result.page)} از ${fa(Math.max(1,Math.ceil(result.total/25)))}</span><div class="row"><button class="btn btn-small btn-outline" id="page-prev" ${state.page===1?'disabled':''}>قبلی</button><button class="btn btn-small btn-outline" id="page-next" ${state.page*25>=result.total?'disabled':''}>بعدی</button></div></div></div>`;
}
let modalSubmit=null;
function showModal(title,content,onSubmit,{wide=false,save='ذخیره تغییرات'}={}){
 const preview=Boolean(state.me?.public_demo);
 modalSubmit=preview?null:onSubmit;
 if(preview){
  content='<div class="notice" role="status" style="margin-bottom:16px"><strong>پیش‌نمایش فرم</strong> — می‌توانید همه فیلدها و مراحل را مشاهده کنید. این نسخه عمومی فقط خواندنی است و اطلاعات ذخیره نمی‌شوند.</div>'+content;
 }
 modals.innerHTML=`<div class="overlay" id="overlay"><div class="modal" role="dialog" aria-modal="true" aria-label="${esc(title)}" style="${wide?'width:min(100%,760px)':''}"><div class="modal-head"><strong>${esc(title)}</strong><button type="button" class="x-btn" id="modal-close" aria-label="بستن">×</button></div><form id="modal-form"><div class="modal-content">${content}</div><div class="modal-footer"><button class="btn btn-light" type="button" id="modal-cancel">انصراف</button>${preview?'<span class="pill good">نمایش بدون ذخیره</span>':`<button class="btn btn-primary" type="submit" id="modal-save">${esc(save)} ${icon('check',16)}</button>`}</div></form></div></div>`;
 $('#modal-form input:not([type=hidden]),#modal-form select')?.focus();
}
function closeModal(){modalSubmit=null;modals.innerHTML=''}
const OPTIONS={status:[['pending','در انتظار'],['shipped','ارسال‌شده'],['delivered','تحویل‌شده'],['returned','مرجوع‌شده']],type:[['cash','نقدی'],['bank','بانک']],role:[['viewer','فقط مشاهده'],['sales','فروش'],['inventory_manager','انباردار'],['accountant','حسابدار'],['admin','مدیر']]};
function selectField(key,items,value,optional=false){
 return `<select class="input" name="${esc(key)}" ${optional?'':'required'}>${optional?'<option value="">انتخاب نشده</option>':''}${items.map(it=>`<option value="${esc(it.id)}" ${it.id===value?'selected':''}>${esc(it.label)}</option>`).join('')}</select>`;
}
async function buildFields(resource,obj={}){
 const m=META[resource];const fields=m.fields||[];
 const refs=[...new Set(fields.map(k=>k==='parent_id'?'categories':REF[k]).filter(Boolean))];
 await Promise.all(refs.map(k=>lookup(k)));
 return `<div class="form-grid">${fields.map(k=>{
   const curr=obj[k]??(BOOLEAN.has(k)?true:'');
   const opt= k==='parent_id'?'categories':REF[k];
   const isRequired=['name','sku','code','product_id','variant_id','list_id','order_id'].includes(k);
   let input;
   if(opt){const arr=(state.lookups[opt]||[]).filter(x=>x.id!==obj.id).map(x=>({id:x.id,label:x.name||x.sku||x.number||x.code}));input=selectField(k,arr,curr,!isRequired)}
   else if(BOOLEAN.has(k))input=selectField(k,[{id:'true',label:'فعال / بله'},{id:'false',label:'غیرفعال / خیر'}],String(curr),false);
   else if(OPTIONS[k])input=selectField(k,OPTIONS[k].map(([id,label])=>({id,label})),curr,false);
   else if(['description','notes','address'].includes(k))input=`<textarea class="input" name="${esc(k)}" rows="3" placeholder="${esc(LABELS[k]||k)}">${esc(curr)}</textarea>`;
   else input=`<input class="input" name="${esc(k)}" ${NUMERIC.has(k)?'type="number" min="0" step="1"':'type="text"'} ${isRequired?'required':''} value="${esc(curr)}" placeholder="${esc(LABELS[k]||k)}" ${k==='image_url'?'dir="ltr"':''}>`;
   return `<div class="field ${['description','notes','address'].includes(k)?'full':''}"><label>${esc(LABELS[k]||k)}</label>${input}</div>`;
 }).join('')}</div>`;
}
function formValues(form,fields){
 const body={};const fd=new FormData(form);
 for(const key of fields){const val=fd.get(key);if(val===''||val==null){if(key in REF || key==='parent_id')body[key]=null;continue}
   if(BOOLEAN.has(key))body[key]=val==='true';
   else if(NUMERIC.has(key))body[key]=Number(val);
   else body[key]=String(val).trim();
 }
 return body;
}
async function openGeneric(resource,id){
 const obj=id?(state.data[resource]||[]).find(x=>x.id===id):null;
 const content=await buildFields(resource,obj||{});
 showModal((obj?'ویرایش ':'ایجاد ')+titleOf(resource),content,async form=>{
   const body=formValues(form,META[resource].fields);
   const result=await api(`data/${resource}${id?'/'+id:''}`,{method:id?'PATCH':'POST',body});
   state.lookups[resource]=null;closeModal();notify(obj?'تغییرات ذخیره شد':'رکورد جدید ثبت شد');loadView();return result;
 },{save:obj?'ذخیره تغییرات':'ثبت رکورد'});
}
async function openTransfer(){
 const [warehouses,variants]=await Promise.all([lookup('warehouses'),lookup('variants')]);
 if(warehouses.length<2||!variants.length){notify('برای انتقال به دو انبار و حداقل یک کالا نیاز دارید',true);return}
 const content=`<div class="form-grid"><div class="field"><label>انبار مبدأ</label>${selectField('source_id',warehouses.map(x=>({id:x.id,label:x.name})),null)}</div><div class="field"><label>انبار مقصد</label>${selectField('destination_id',warehouses.map(x=>({id:x.id,label:x.name})),null)}</div><div class="field"><label>کالا / تنوع</label>${selectField('variant_id',variants.map(x=>({id:x.id,label:`${x.sku} - ${x.name}`})),null)}</div><div class="field"><label>تعداد</label><input class="input" type="number" min="1" step="1" value="1" name="quantity" required></div></div><p class="notice">پس از ثبت انتقال، ابتدا «ارسال» و سپس «دریافت» را بزنید؛ هر مرحله به‌صورت جداگانه در گردش انبار ثبت می‌شود.</p>`;
 showModal('انتقال بین انبارها',content,async form=>{
  const f=new FormData(form),body={source_id:f.get('source_id'),destination_id:f.get('destination_id'),variant_id:f.get('variant_id'),quantity:Number(f.get('quantity'))};
  await api('transfers',{method:'POST',body});closeModal();notify('انتقال پیش‌نویس ایجاد شد');loadView();
 },{save:'ثبت انتقال'});
}
const serialList=(raw)=>String(raw||'').split(/[\\n,،;]+/).map(x=>x.trim()).filter(Boolean);
async function openRegisterSerials(){
 const [warehouses,variants]=await Promise.all([lookup('warehouses'),lookup('variants')]);
 const tracked=variants.filter(x=>x.track_serial);
 if(!tracked.length)return notify('ابتدا ردیابی شماره سریال را برای یک کالا فعال کنید',true);
 const content=`<div class="form-grid">
 <div class="field"><label>انبار</label>${selectField('warehouse_id',warehouses.map(x=>({id:x.id,label:x.name})))}</div>
 <div class="field"><label>کالا با ردیابی سریال</label>${selectField('variant_id',tracked.map(x=>({id:x.id,label:x.sku})))}</div>
 <div class="field full"><label>شماره سریال‌ها (هر خط یک شماره)</label><textarea class="input" name="serials" rows="7" required></textarea></div></div>
 <p class="notice">این عملیات فقط شماره‌های منحصربه‌فرد را به موجودی قبلاً ثبت‌شده متصل می‌کند؛ موجودی کل را تغییر نمی‌دهد.</p>`;
 showModal('شناسایی شماره سریال',content,async form=>{
  const fd=new FormData(form),serials=serialList(fd.get('serials'));
  await api('serials/register',{method:'POST',body:{warehouse_id:fd.get('warehouse_id'),variant_id:fd.get('variant_id'),serials}});
  closeModal();notify('شماره سریال‌ها ثبت شدند');loadView();
 },{save:'ثبت سریال‌ها'});
}
async function openReceivePurchase(id){
 const [doc,variants]=await Promise.all([api('documents/purchases/'+id+'/lines'),lookup('variants')]);
 const rows=doc.items.filter(x=>x.received<x.quantity);
 if(!rows.length)return notify('همه اقلام سفارش دریافت شده‌اند',true);
 const content=`<p class="notice">برای کالاهای بچ‌دار، شماره بچ و تاریخ انقضا را وارد کنید. برای کالای سریالی، سریال‌های هر واحد الزامی است.</p>
 ${rows.map(line=>{
   const v=variants.find(x=>x.id===line.variant_id);
   return `<div class="panel panel-padded receive-line" data-id="${esc(line.id)}" style="margin-top:10px">
   <strong>${esc(v?.sku||line.variant_id)}</strong> <span class="muted">مانده ${fa(line.quantity-line.received)} عدد</span>
   <div class="form-grid" style="margin-top:10px"><div class="field"><label>تعداد دریافتی</label><input class="input r-qty" type="number" min="0" max="${line.quantity-line.received}" value="${line.quantity-line.received}" required></div>
   <div class="field"><label>شماره بچ ${v?.track_batch?'(الزامی)':''}</label><input class="input r-lot" maxlength="100" ${v?.track_batch?'required':''}></div>
   <div class="field"><label>تاریخ انقضا (اختیاری)</label><input class="input r-expiry" type="date"></div>
   <div class="field full"><label>سریال‌ها (هر خط یک شماره) ${v?.track_serial?'(الزامی)':''}</label><textarea class="input r-serials" rows="2"></textarea></div></div></div>`;
 }).join('')}`;
 showModal('دریافت کالا از تأمین‌کننده',content,async form=>{
  const items=$('.receive-line',form).map(line=>({
    line_id:line.dataset.id,quantity:Number(line.querySelector('.r-qty').value),
    lot:line.querySelector('.r-lot').value.trim(),
    expiry_date:line.querySelector('.r-expiry').value||null,
    serials:serialList(line.querySelector('.r-serials').value)
  })).filter(x=>x.quantity>0);
  if(!items.length)throw Error('تعداد دریافتی را وارد کنید');
  await api('purchases/'+id+'/receive',{method:'POST',body:{items,idempotency_key:uid()}});
  closeModal();notify('دریافت جزئی یا کامل ثبت شد');loadView();
 },{save:'ثبت رسید کالا',wide:true});
}

async function openAdjustment(){
 const [warehouses,variants]=await Promise.all([lookup('warehouses'),lookup('variants')]);
 if(!warehouses.length||!variants.length){notify('ابتدا کالا و انبار ثبت کنید',true);return}
 const reasons=[['opening','موجودی اولیه'],['correction','اصلاح موجودی'],['damage','آسیب‌دیدگی'],['loss','کسری'],['cycle_count','انبارگردانی']];
 const content=`<div class="form-grid"><div class="field"><label>انبار</label>${selectField('warehouse_id',warehouses.map(x=>({id:x.id,label:x.name})),null)}</div><div class="field"><label>کالا</label>${selectField('variant_id',variants.map(x=>({id:x.id,label:`${x.sku} - ${x.name}`})),null)}</div><div class="field"><label>تغییر موجودی</label><input class="input" type="number" step="1" name="delta" placeholder="مثلاً ۱۰ یا ۳-" required></div><div class="field"><label>علت</label>${selectField('reason',reasons.map(([id,label])=>({id,label})),null)}</div><div class="field full"><label>توضیحات (اختیاری)</label><textarea class="input" name="note" rows="2"></textarea></div><div class="field"><label>شماره بچ</label><input class="input" name="lot" maxlength="100"></div><div class="field"><label>تاریخ انقضا</label><input class="input" name="expiry_date" type="date"></div><div class="field full"><label>سریال‌ها (هر خط یک شماره)</label><textarea class="input" name="serials" rows="3"></textarea></div></div><p class="notice">تعداد مثبت موجودی را افزایش و تعداد منفی آن را کاهش می‌دهد. موجودی هیچ‌وقت منفی نخواهد شد.</p>`;
 showModal('اصلاح موجودی انبار',content,async form=>{
  const f=new FormData(form);await api('stock/adjust',{method:'POST',body:{warehouse_id:f.get('warehouse_id'),variant_id:f.get('variant_id'),delta:Number(f.get('delta')),reason:f.get('reason'),note:f.get('note'),lot:f.get('lot'),expiry_date:f.get('expiry_date')||null,serials:serialList(f.get('serials'))}});
  closeModal();notify('موجودی با موفقیت اصلاح شد');loadView();
 },{save:'ثبت تغییر موجودی'});
}
async function openDocument(kind){
 const purchase=kind==='purchases';
 const [warehouses,variants,contacts]=await Promise.all([lookup('warehouses'),lookup('variants'),lookup(purchase?'suppliers':'customers')]);
 if(!warehouses.length||!variants.length||(purchase&&!contacts.length)){notify('ابتدا کالا، انبار و اطلاعات مرتبط را ثبت کنید',true);return}
 const contactsOptions=contacts.map(x=>({id:x.id,label:x.name}));
 const opts=variants.filter(x=>x.active).map(x=>({id:x.id,label:`${x.sku} - ${x.name}`,cost:x.purchase_cost,price:x.retail_price}));
 const line=()=>`<div class="items-editor item-line"><select class="input item-variant" required>${opts.map(x=>`<option value="${esc(x.id)}">${esc(x.label)}</option>`).join('')}</select><input class="input item-qty" type="number" min="1" value="1" required><input class="input item-price money" type="number" min="0" placeholder="قیمت پیش‌فرض"><button class="btn btn-light remove-item" type="button" title="حذف این قلم">${icon('x',14)}</button></div>`;
 const content=`<div class="form-grid"><div class="field"><label>انبار</label>${selectField('warehouse_id',warehouses.map(x=>({id:x.id,label:x.name})))}</div><div class="field"><label>${purchase?'تأمین‌کننده':'مشتری'}</label>${selectField(purchase?'supplier_id':'customer_id',contactsOptions,null,!purchase)}</div>${purchase?'':`<div class="field"><label>کانال فروش</label>${selectField('channel',[{id:'retail',label:'خرده‌فروشی'},{id:'wholesale',label:'عمده'},{id:'online',label:'آنلاین'},{id:'pos',label:'حضوری'}])}</div><div class="field"><label>تخفیف کل (تومان)</label><input name="discount" class="input" type="number" min="0" value="0"></div>`}</div><div class="modal-divider"></div><div class="between"><strong>اقلام سفارش</strong><button class="btn btn-small btn-light" type="button" id="new-line">افزودن قلم ${icon('plus',15)}</button></div><div class="line-header">کالا / تعداد / قیمت اختیاری (تومان)</div><div id="items-list">${line()}</div><p class="hint">اگر قیمت را خالی بگذارید، نرخ ثبت‌شده برای کالا استفاده می‌شود.</p>`;
 showModal(purchase?'ایجاد سفارش خرید':'ثبت سفارش فروش',content,async form=>{
  const f=new FormData(form);
  const items=$$('.item-line',form).map(row=>{
   const p=row.querySelector('.item-price').value.trim();
   return {variant_id:row.querySelector('.item-variant').value,quantity:Number(row.querySelector('.item-qty').value),...(p!==''?{[purchase?'cost':'price']:Number(p)}:{})};
  });
  const body={warehouse_id:f.get('warehouse_id'),items};
  if(purchase)body.supplier_id=f.get('supplier_id');
  else {body.customer_id=f.get('customer_id')||null;body.channel=f.get('channel');body.discount=Number(f.get('discount')||0)}
  await api(kind,{method:'POST',body});closeModal();notify('سفارش ثبت شد');loadView();
 },{wide:true,save:'ثبت سفارش'});
 const btn=$('#new-line');btn.addEventListener('click',()=>$('#items-list').insertAdjacentHTML('beforeend',line()));
 $('#items-list').addEventListener('click',e=>{const remove=e.target.closest('.remove-item');if(remove && $$('.item-line').length>1)remove.closest('.item-line').remove()});
}
async function openPayment(kind,id){
 const purchase=kind==='purchase';
 const doc=(state.data[purchase?'purchases':'sales']||[]).find(x=>x.id===id);
 if(!doc)return notify('سند یافت نشد',true);
 const accounts=await lookup('cash-accounts');
 const remaining=Math.max(0,doc.total-doc.paid);
 const content=`<div class="notice">شماره سند ${esc(doc.number)} — مانده قابل پرداخت: <b>${money(remaining)}</b></div><div class="form-grid" style="margin-top:18px"><div class="field"><label>مبلغ (تومان)</label><input class="input" type="number" name="amount" min="1" max="${remaining}" value="${remaining}" required></div><div class="field"><label>روش پرداخت</label>${selectField('method',[{id:'cash',label:'نقدی'},{id:'card',label:'کارت'},{id:'transfer',label:'حواله'},{id:'online',label:'آنلاین (ثبت دستی)'}])}</div><div class="field full"><label>ثبت در حساب (اختیاری)</label>${selectField('account_id',accounts.map(x=>({id:x.id,label:x.name})),null,true)}</div></div><p class="hint">پرداخت آنلاین فعلاً فقط ثبت دستی است؛ درگاه پرداخت متصل نشده است.</p>`;
 showModal('ثبت پرداخت',content,async form=>{
  const f=new FormData(form);const body={amount:Number(f.get('amount')),method:f.get('method'),account_id:f.get('account_id')||null,idempotency_key:uid(),[purchase?'purchase_id':'sale_id']:id};
  await api('payments',{method:'POST',body});closeModal();notify('پرداخت ثبت شد و اعلان آن ایجاد شد');loadView();
 },{save:'ثبت پرداخت'});
}
async function openReturnSettlement(id){
 const [balance,accounts]=await Promise.all([api('returns/'+encodeURIComponent(id)+'/settlement'),lookup('cash-accounts')]);
 if(balance.remaining<=0)return notify('این مرجوعی مانده قابل تسویه ندارد',true);
 if(!accounts.length)return notify('ابتدا یک حساب نقدی یا بانکی ثبت کنید',true);
 const content=`<div class="notice">سند ${esc(balance.document_number)} — ${balance.direction==='sale'?'بازپرداخت به مشتری':'دریافت از تأمین‌کننده'}
 <strong>${money(balance.remaining)}</strong> مانده دارد.</div>
 <div class="form-grid" style="margin-top:16px"><div class="field"><label>مبلغ تسویه (تومان)</label>
 <input class="input" name="amount" type="number" required min="1" step="1" max="${balance.remaining}" value="${balance.remaining}"></div>
 <div class="field"><label>حساب ثبت وجه</label>${selectField('account_id',accounts.map(x=>({id:x.id,label:x.name})))}</div></div>
 <p class="hint">این عملیات صرفاً تسویه دستی را در حساب‌های ERP ثبت می‌کند؛ به درگاه بانکی متصل نیست.</p>`;
 showModal('تسویه مرجوعی',content,async form=>{
  const f=new FormData(form);
  await api('returns/'+encodeURIComponent(id)+'/settle',{method:'POST',
    body:{amount:Number(f.get('amount')),account_id:f.get('account_id'),idempotency_key:uid()}});
  closeModal();notify('تسویه مرجوعی ثبت شد');loadView();
 },{save:'ثبت تسویه'});
}

async function openReturn(kind,id){
 const purchase=kind==='purchase';
 const data=await api(`documents/${purchase?'purchases':'sales'}/${id}/lines`);
 const variants=await lookup('variants');
 if(!data.items.length)return notify('سند بدون ردیف است',true);
 const opts=data.items.map(x=>({id:x.variant_id,label:(variants.find(v=>v.id===x.variant_id)?.sku||x.variant_id.slice(0,8))+' / '+fa(x.quantity)+' عدد'}));
 const content=`<div class="notice">مرجوعی به سند اصلی متصل می‌شود و تاریخچه تغییرات قابل ردیابی خواهد بود.</div><div class="form-grid" style="margin-top:18px"><div class="field"><label>کالا</label>${selectField('variant_id',opts)}</div><div class="field"><label>تعداد مرجوعی</label><input class="input" type="number" name="quantity" min="1" value="1" required></div>${purchase?'':`<div class="field full"><label>بازگشت کالا به موجودی</label>${selectField('restock',[{id:'true',label:'بله، کالا سالم است'},{id:'false',label:'خیر، کالا معیوب است'}])}</div>`}<div class="field full"><label>سریال‌های کالای برگشتی (برای کالاهای سریالی، هر خط یک شماره)</label><textarea class="input" name="serials" rows="3"></textarea></div></div>`;
 showModal('ثبت مرجوعی '+(purchase?'خرید':'فروش'),content,async form=>{
  const f=new FormData(form);
  await api('returns',{method:'POST',body:{direction:purchase?'purchase':'sale',order_id:id,variant_id:f.get('variant_id'),quantity:Number(f.get('quantity')),restock:purchase?false:f.get('restock')==='true',serials:serialList(f.get('serials')),idempotency_key:uid()}});
  closeModal();notify('مرجوعی ثبت شد');loadView();
 },{save:'ثبت مرجوعی'});
}
const REPORT_TYPES=[['sales','عملکرد فروش'],['inventory','ارزش موجودی'],['margins','حاشیه سود'],['receivables','مطالبات'],['payables','بدهی خرید']];
async function renderFulfillments(){
 const d=await api('fulfillments?page='+state.page+'&limit=30');
 const rows=d.items.map(x=>`<tr><td>${esc(x.number)}</td><td>${esc(x.order_id)}</td>
 <td>${money(x.revenue)}</td><td>${dateFa(x.created_at)}</td>
 <td>${status(x.status)}</td><td><button class="btn btn-small btn-outline" data-fulfillment-details="${esc(x.id)}">جزئیات ${icon('file',14)}</button></td></tr>`).join('');
 $('#page-content').innerHTML=`${head('محموله‌ها و ارسال جزئی',
 'مشاهده محموله‌های ثبت‌شده و اقلام هر ارسال؛ برای هر سفارش می‌توان چند بار ارسال کرد')}
 <div class="panel"><div class="table-wrap"><table class="table"><thead><tr><th>شماره محموله</th><th>شناسه سفارش</th>
 <th>ارزش ارسالی</th><th>تاریخ</th><th>وضعیت</th><th>جزئیات</th></tr></thead>
 <tbody>${rows||'<tr><td colspan="6" class="muted">محموله‌ای ثبت نشده است.</td></tr>'}</tbody></table></div>
 <div class="pagination"><span>${fa(d.total)} محموله · صفحه ${fa(state.page)}</span>
 <div class="row"><button class="btn btn-small btn-outline" id="fulfill-prev" ${state.page<=1?'disabled':''}>قبلی</button>
 <button class="btn btn-small btn-outline" id="fulfill-next" ${state.page*30>=d.total?'disabled':''}>بعدی</button></div></div></div>
 <p class="hint">در هر ارسال مقدار رزروشده آزاد و به همان میزان موجودی کسر می‌شود. دفتر کل و تاریخچه انبار جداگانه ثبت می‌شوند.</p>`;
}
async function openFulfillmentDetails(id){
 const d=await api('fulfillments?page=1&limit=100');
 const obj=d.items.find(x=>x.id===id);
 if(!obj)return notify('محموله یافت نشد',true);
 const variants=await lookup('variants');
 const rows=(obj.items||[]).map(line=>`<tr><td>${esc(variants.find(x=>x.id===line.variant_id)?.sku||line.variant_id)}</td>
 <td>${fa(line.quantity)}</td><td>${money(line.unit_price)}</td></tr>`).join('');
 const form=`<div class="notice">محموله: ${esc(obj.number)} — وضعیت ${esc(obj.status)}</div>
 <div class="table-wrap"><table class="table"><thead><tr><th>کالا</th><th>تعداد</th><th>قیمت</th></tr></thead>
 <tbody>${rows}</tbody></table></div><p class="hint">شرکت حمل: ${esc(obj.carrier||'—')} | رهگیری: ${esc(obj.tracking_number||'—')}</p>
 ${roleCan('shipments')&&obj.status!=='delivered'?`<div class="form-grid"><div class="field"><label>شرکت حمل</label><input class="input" name="carrier" maxlength="120" value="${esc(obj.carrier||'')}"></div>
 <div class="field"><label>کد رهگیری</label><input class="input" name="tracking_number" maxlength="120" value="${esc(obj.tracking_number||'')}"></div>
 <div class="field"><label>وضعیت</label>${selectField('status',[{id:'shipped',label:'ارسال شده'},{id:'delivered',label:'تحویل شده'}],obj.status)}</div></div>`:''}`;
 showModal('جزئیات محموله',form,async modal=>{
  if(roleCan('shipments')&&obj.status!=='delivered'){
   const fd=new FormData(modal);
   await api('fulfillments/'+encodeURIComponent(id),{method:'PATCH',body:{
     carrier:fd.get('carrier'),tracking_number:fd.get('tracking_number'),status:fd.get('status')}});
  }
  closeModal();notify('جزئیات محموله بررسی شد');renderFulfillments();
 },{save:roleCan('shipments')&&obj.status!=='delivered'?'ذخیره ارسال':'بستن'});
}
async function openPartialFulfill(id){
 const [doc,variants]=await Promise.all([
   api('documents/sales/'+encodeURIComponent(id)+'/lines'),lookup('variants')]);
 const rows=doc.items.filter(x=>x.fulfilled<x.quantity);
 if(!rows.length)return notify('تمام سفارش تحویل شده است',true);
 const html=`<div class="notice">تعداد باقی‌مانده از سفارش را برای ارسال انتخاب کنید. چند محموله برای یک سفارش مجاز است.</div>
 ${rows.map(x=>`<div class="field partial-line" data-id="${esc(x.id)}" style="margin-top:12px">
 <label>${esc(variants.find(v=>v.id===x.variant_id)?.sku||x.variant_id)} — مانده ${fa(x.quantity-x.fulfilled)} عدد</label>
 <input class="input" type="number" min="0" max="${x.quantity-x.fulfilled}" step="1" value="${x.quantity-x.fulfilled}"></div>`).join('')}`;
 showModal('ثبت ارسال جزئی',html,async form=>{
  const items=$('.partial-line',form).map(row=>({
     line_id:row.dataset.id,quantity:Number(row.querySelector('input').value)
  })).filter(x=>x.quantity>0);
  if(!items.length)throw Error('حداقل یک قلم برای ارسال انتخاب کنید');
  await api('sales/'+encodeURIComponent(id)+'/fulfill-partial',{method:'POST',
      body:{items,idempotency_key:uid()}});
  closeModal();notify('محموله ثبت شد؛ موجودی و حسابداری به‌روزرسانی شدند');loadView();
 },{save:'ثبت ارسال',wide:true});
}

async function renderInvoices(){
 const result=await api('invoices?page='+state.page+'&limit=25');
 const btn=(roleCan('sales')||roleCan('cash-accounts'))?
   `<button class="btn btn-primary" id="issue-invoice">صدور فاکتور جدید ${icon('plus',17)}</button>`:'';
 const items=result.items.map(inv=>`<tr><td><strong>${esc(inv.number)}</strong></td>
 <td>${esc(inv.customer_name)}</td><td>${dateFa(inv.created_at)}</td>
 <td>${money(inv.total)}</td><td><a class="btn btn-small btn-outline" href="/api/invoices/${encodeURIComponent(inv.id)}/print" target="_blank" rel="noopener noreferrer">چاپ ${icon('file',14)}</a></td></tr>`).join('');
 const cards=result.items.map(inv=>`<div class="mobile-card"><div class="between"><strong>${esc(inv.number)}</strong><span>${money(inv.total)}</span></div>
 <div class="mobile-fields"><div><label>مشتری</label>${esc(inv.customer_name)}</div><div><label>تاریخ</label>${dateFa(inv.created_at)}</div></div>
 <div class="row"><a class="btn btn-small btn-outline" href="/api/invoices/${encodeURIComponent(inv.id)}/print" target="_blank" rel="noopener noreferrer">چاپ فاکتور ${icon('file',14)}</a></div></div>`).join('');
 $('#page-content').innerHTML=`${head('فاکتورهای فروش','فاکتورهای داخلی با نسخه ثابت اطلاعات کالا و مبلغ',btn)}
 <div class="panel"><div class="notice" style="margin:16px">این بخش فاکتور داخلی است، نه فاکتور رسمی تأییدشده مالیاتی.</div>
 ${result.items.length?`<div class="table-wrap"><table class="table"><thead><tr><th>شماره</th><th>مشتری</th><th>تاریخ</th><th>مبلغ</th><th>چاپ</th></tr></thead>
 <tbody>${items}</tbody></table></div><div class="mobile-cards">${cards}</div>`:'<div class="empty">تاکنون فاکتوری صادر نشده است.</div>'}
 <div class="pagination"><span>${fa(result.total)} فاکتور · صفحه ${fa(state.page)}</span>
 <div class="row"><button class="btn btn-small btn-outline" id="invoice-prev" ${state.page<=1?'disabled':''}>قبلی</button>
 <button class="btn btn-small btn-outline" id="invoice-next" ${state.page*25>=result.total?'disabled':''}>بعدی</button></div></div></div>`;
}
async function openIssueInvoice(){
 const sales=await api('data/sales?limit=100');
 const eligible=sales.items.filter(x=>['confirmed','fulfilled'].includes(x.status));
 if(!eligible.length)return notify('ابتدا یک سفارش فروش را تأیید کنید',true);
 const content=`<div class="field"><label>سفارش فروش</label>${selectField('order_id',eligible.map(x=>({id:x.id,label:x.number+' — '+money(x.total)})))}</div>
 <p class="notice">پس از صدور، اطلاعات فروش و قیمت اقلام در فاکتور ثابت می‌مانند. برای هر فروش تنها یک فاکتور صادر می‌شود.</p>
 <p class="hint">این سند داخلی است و برای صدور فاکتور رسمی مالیاتی باید الزامات قانونی جداگانه اجرا شوند.</p>`;
 showModal('صدور فاکتور داخلی',content,async form=>{
  const id=new FormData(form).get('order_id');
  const result=await api('invoices',{method:'POST',body:{order_id:id}});
  closeModal();notify(result.duplicate?'این فروش قبلاً فاکتور داشته است':'فاکتور صادر شد');renderInvoices();
 },{save:'صدور فاکتور'});
}

const LEDGER_KINDS={asset:'دارایی',liability:'بدهی',equity:'سرمایه',revenue:'درآمد',expense:'هزینه'};
async function renderLedger(){
 const v=state.view;
 const main=$('#page-content');
 const canWrite=roleCan('cash-accounts');
 if(v==='ledger-accounts'){
  const data=await api('ledger/accounts');
  main.innerHTML=`${head('کدینگ حسابداری','دفتر کل بر پایه ثبت دوطرفه در واحد تومان',
   canWrite?`<button class="btn btn-primary" id="ledger-new-account">حساب جدید ${icon('plus',16)}</button>`:'')}
   ${!data.total&&canWrite?`<button class="btn btn-outline" id="ledger-setup">ساخت کدینگ استاندارد ${icon('plus',15)}</button>`:''}
   <div class="panel"><div class="table-wrap"><table class="table"><thead><tr><th>کد</th><th>نام حساب</th><th>ماهیت</th><th>وضعیت</th></tr></thead>
   <tbody>${data.items.map(a=>`<tr><td>${esc(a.code)}</td><td>${esc(a.name)}</td><td>${esc(LEDGER_KINDS[a.kind]||a.kind)}</td><td>${a.active?'فعال':'غیرفعال'}</td></tr>`).join('')}
   </tbody></table></div></div>`;
 }else if(v==='ledger-journals'){
  const result=await api('ledger/journals?page='+state.page+'&limit=40');
  main.innerHTML=`${head('اسناد حسابداری','اسناد ثبت‌شده تغییرناپذیر هستند و باید تراز باشند',
   canWrite?`<button class="btn btn-primary" id="ledger-new-journal">سند جدید ${icon('plus',16)}</button>`:'')}
   <div class="panel"><div class="table-wrap"><table class="table"><thead><tr><th>شماره سند</th><th>تاریخ</th><th>شرح</th><th>عملیات</th></tr></thead>
   <tbody>${result.items.map(j=>`<tr><td>${esc(j.number)}</td><td>${dateFa(j.journal_date)}</td><td>${esc(j.memo)}</td>
   <td><button class="btn btn-small btn-outline" data-journal-detail="${esc(j.id)}">مشاهده ردیف‌ها ${icon('file',14)}</button></td></tr>`).join('')}</tbody></table></div>
   <div class="pagination"><span>${fa(result.total)} سند · صفحه ${fa(state.page)}</span>
   <div class="row"><button class="btn btn-small btn-outline" id="ledger-prev" ${state.page<=1?'disabled':''}>قبلی</button>
   <button class="btn btn-small btn-outline" id="ledger-next" ${state.page*40>=result.total?'disabled':''}>بعدی</button></div></div></div>`;
 }else if(v==='ledger-balance'){
  const data=await api('ledger/trial-balance');
  main.innerHTML=`${head('تراز آزمایشی','جمع ستون‌های بدهکار و بستانکار باید برابر باشد')}
   <div class="metric-grid"><div class="panel metric-card"><div class="label">جمع بدهکار</div><strong class="num">${money(data.total_debit)}</strong></div>
   <div class="panel metric-card"><div class="label">جمع بستانکار</div><strong class="num">${money(data.total_credit)}</strong></div>
   <div class="panel metric-card"><div class="label">وضعیت تراز</div><strong class="num">${data.balanced?'متوازن':'نامتوازن'}</strong></div></div>
   <div class="panel"><div class="table-wrap"><table class="table"><thead><tr><th>حساب</th><th>نام</th><th>بدهکار</th><th>بستانکار</th><th>مانده</th></tr></thead>
   <tbody>${data.items.map(x=>`<tr><td>${esc(x.code)}</td><td>${esc(x.name)}</td><td>${money(x.debit)}</td>
   <td>${money(x.credit)}</td><td>${money(x.balance)}</td></tr>`).join('')}</tbody></table></div></div>`;
 }else if(v==='ledger-profit'){
  const p=await api('ledger/profit-loss');
  main.innerHTML=`${head('صورت سود و زیان','بر اساس اسناد قطعی دوطرفه؛ همه اعداد به تومان')}
   <div class="metric-grid"><div class="panel metric-card"><div class="label">درآمد خالص</div><strong class="num">${money(p.revenue)}</strong></div>
   <div class="panel metric-card"><div class="label">جمع هزینه‌ها</div><strong class="num">${money(p.expenses)}</strong></div>
   <div class="panel metric-card"><div class="label">سود/زیان خالص</div><strong class="num">${money(p.net_profit)}</strong></div></div>
   <div class="panel"><div class="table-wrap"><table class="table"><thead><tr><th>کد</th><th>حساب</th><th>طبقه</th><th>مانده</th></tr></thead>
   <tbody>${p.account_totals.map(a=>`<tr><td>${esc(a.code)}</td><td>${esc(a.name)}</td>
   <td>${esc(LEDGER_KINDS[a.kind]||a.kind)}</td><td>${money(a.balance)}</td></tr>`).join('')}</tbody></table></div></div>
   <p class="hint">داده‌های نمونه برای نمایش نحوه محاسبه هستند. گزارش مالیاتی رسمی نیازمند تنظیمات قانونی کسب‌وکار است.</p>`;
 }
}
async function openLedgerDetails(id){
 const [doc,accts]=await Promise.all([api('ledger/journals/'+encodeURIComponent(id)),api('ledger/accounts')]);
 const byId=Object.fromEntries(accts.items.map(a=>[a.id,a]));
 const rows=doc.lines.map(x=>`<tr><td>${esc(byId[x.account_id]?.code||'—')}</td><td>${esc(byId[x.account_id]?.name||'—')}</td>
 <td>${money(x.debit)}</td><td>${money(x.credit)}</td></tr>`).join('');
 showModal('سند '+doc.journal.number,`<div class="notice">${esc(doc.journal.memo)} · ${dateFa(doc.journal.journal_date)}</div>
 <div class="table-wrap" style="margin-top:16px"><table class="table"><thead><tr><th>کد</th><th>حساب</th><th>بدهکار</th><th>بستانکار</th></tr></thead>
 <tbody>${rows}</tbody></table></div>`,async()=>closeModal(),{save:'بستن'});
}
function openLedgerAccount(){
 showModal('حساب جدید',`<div class="form-grid"><div class="field"><label>کد حساب</label><input class="input" name="code" pattern="[0-9]+" required maxlength="20"></div>
 <div class="field"><label>نام حساب</label><input class="input" name="name" required maxlength="180"></div>
 <div class="field full"><label>ماهیت حساب</label>${selectField('kind',Object.entries(LEDGER_KINDS).map(([id,label])=>({id,label})))}</div></div>`,
 async form=>{const f=new FormData(form);await api('ledger/accounts',{method:'POST',body:{code:f.get('code'),name:f.get('name'),kind:f.get('kind')}});
 closeModal();notify('حساب جدید ثبت شد');renderLedger()},{save:'ثبت حساب'});
}
async function openLedgerJournal(){
 const {items:accounts}=await api('ledger/accounts');
 if(accounts.length<2)return notify('ابتدا حساب‌های دفتر کل را ایجاد کنید',true);
 const choose=(key)=>selectField(key,accounts.map(x=>({id:x.id,label:x.code+' - '+x.name})));
 const content=`<div class="notice">سند باید جمع بدهکار و بستانکار یکسان داشته باشد. پس از ثبت، تغییر نمی‌کند.</div>
 <div class="field" style="margin-top:14px"><label>شرح سند</label><input class="input" name="memo" required maxlength="900"></div>
 <div class="form-grid" style="margin-top:16px">
 <div class="field full"><strong>ردیف بدهکار</strong></div><div class="field full">${choose('account_debit')}</div>
 <div class="field"><label>مبلغ بدهکار (تومان)</label><input class="input" type="number" name="debit" min="1" step="1" required></div>
 <div class="field full"><strong>ردیف بستانکار</strong></div><div class="field full">${choose('account_credit')}</div>
 <div class="field"><label>مبلغ بستانکار (تومان)</label><input class="input" type="number" name="credit" min="1" step="1" required></div></div>`;
 showModal('ثبت سند حسابداری',content,async form=>{
  const f=new FormData(form),debit=Number(f.get('debit')),credit=Number(f.get('credit'));
  if(!Number.isSafeInteger(debit)||!Number.isSafeInteger(credit)||debit<=0||debit!==credit)throw Error('مبلغ دو طرف باید صحیح، مثبت و برابر باشد');
  const lines=[{account_id:f.get('account_debit'),debit,credit:0},
               {account_id:f.get('account_credit'),debit:0,credit}];
  if(lines[0].account_id===lines[1].account_id)throw Error('حساب بدهکار و بستانکار باید متفاوت باشند');
  await api('ledger/journals',{method:'POST',body:{memo:f.get('memo'),lines,idempotency_key:uid()}});
  closeModal();notify('سند تراز ثبت شد');renderLedger();
 },{save:'ثبت سند'});
}

async function renderSecurity(){
 const demo=!!state.me.public_demo;
 const data=demo?{items:[]}:(await api('auth/sessions'));
 $('#page-content').innerHTML=`${head('امنیت حساب و نشست‌ها','مدیریت نشست‌های فعال و تعویض رمز عبور',
 !demo?`<button class="btn btn-primary" id="security-change-password">تغییر رمز عبور ${icon('edit',16)}</button>`:'')}
 ${demo?'<div class="notice">دموی عمومی فقط برای مشاهده است. مدیریت رمز عبور و نشست کاربر واقعی پس از فعال‌سازی حساب اختصاصی در دسترس قرار می‌گیرد.</div>':''}
 <div class="panel"><div class="table-wrap"><table class="table"><thead><tr><th>زمان ایجاد</th><th>انقضا</th><th>وضعیت</th><th>عملیات</th></tr></thead>
 <tbody>${data.items.map(x=>`<tr><td>${dateFa(x.created_at)}</td><td>${dateFa(x.expires_at)}</td>
 <td>${x.revoked?'<span class="pill bad">لغوشده</span>':'<span class="pill good">معتبر</span>'}</td>
 <td>${x.revoked?'—':`<button class="btn btn-small btn-danger" data-revoke-session="${esc(x.id)}">لغو نشست ${icon('x',14)}</button>`}</td></tr>`).join('')}
 ${demo?'<tr><td>۱۴۰۵/۰۸/۱۶</td><td>۱۴۰۵/۰۸/۲۳</td><td><span class="pill good">نمونه نشست معتبر</span></td><td>فقط مشاهده</td></tr>':''}
 </tbody></table></div></div>
 <div class="notice" style="margin-top:18px">نشست‌ها با کوکی امن و شناسه قابل لغو مدیریت می‌شوند. پس از تغییر رمز عبور، همه نشست‌های قبلی قطع می‌شوند.</div>`;
}
function openChangePassword(){
 if(state.me.public_demo)return notify('دموی عمومی قابل تغییر نیست',true);
 const content=`<div class="form-grid"><div class="field full"><label>رمز عبور فعلی</label>
 <input class="input" type="password" name="current_password" required></div>
 <div class="field full"><label>رمز عبور جدید (حداقل ۱۲ نویسه)</label>
 <input class="input" type="password" name="new_password" required minlength="12" maxlength="200"></div>
 <div class="field full"><label>تکرار رمز جدید</label>
 <input class="input" type="password" name="repeat_password" required minlength="12" maxlength="200"></div></div>`;
 showModal('تغییر رمز عبور',content,async form=>{
  const f=new FormData(form);
  if(f.get('new_password')!==f.get('repeat_password'))throw Error('تکرار رمز عبور مطابقت ندارد');
  await api('auth/password/change',{method:'POST',body:{
     current_password:f.get('current_password'),new_password:f.get('new_password')}});
  closeModal();state.me=null;renderAuth();notify('رمز عبور تغییر کرد؛ دوباره وارد شوید');
 },{save:'تغییر رمز'});
}

async function renderIntegrations(){
 const data=await api('integrations');state.data.integrations=data.items;
 const allowed=!state.me.public_demo&&['owner','admin'].includes(state.me.role);
 $('#page-content').innerHTML=`${head('اتصالات و زیرساخت','بخش آماده‌سازی سرویس‌هایی که بعداً تهیه می‌کنید')}
 <div class="notice" style="margin-bottom:20px">این سرویس‌ها هنوز فعال نیستند و هیچ پیامک، پرداخت بانکی، فایل یا سفارش واقعی ارسال نمی‌شود. کلیدهای محرمانه فقط به‌صورت متغیر محیطی روی سرور ذخیره خواهند شد.</div>
 <div class="metric-grid">${data.items.map(x=>`<div class="panel panel-padded">
 <div class="between"><div><div class="panel-title">${esc(x.label)}</div><div class="panel-sub">سرویس: ${esc(x.provider||'انتخاب نشده')}</div></div><span class="pill">منتظر اتصال</span></div>
 <p class="hint">برای فعال‌سازی نهایی به سرویس و اطلاعات اتصال نیاز است. رمز یا API Key در فرم عمومی دریافت نمی‌شود.</p>
 <div class="between"><small>متغیر موردنیاز: <code dir="ltr">${esc(x.required_env)}</code></small>
 ${allowed?`<button class="btn btn-small btn-outline" data-configure-integration="${esc(x.kind)}">تنظیمات آماده‌سازی ${icon('settings',14)}</button>`:''}</div></div>`).join('')}</div>`;
}
function openConfigureIntegration(kind){
 const it=(state.data.integrations||[]).find(x=>x.kind===kind);if(!it)return;
 const html=`<div class="notice">پیکربندی غیرمحرمانه ثبت می‌شود. اتصال واقعی فقط پس از تهیه سرویس، تعریف رمز در سرور و تست آداپتور فعال خواهد شد.</div>
 <div class="form-grid" style="margin-top:16px"><div class="field full"><label>ارائه‌دهنده</label>
 ${selectField('provider',it.providers.map(x=>({id:x,label:x})),it.provider)}</div>
 ${it.fields.map(k=>`<div class="field full"><label>${esc(k)}</label><input class="input" type="text" name="${esc(k)}" maxlength="300" value="${esc(it.settings[k]||'')}" dir="ltr"></div>`).join('')}</div>`;
 showModal('تنظیمات '+it.label,html,async form=>{
  const fd=new FormData(form),settings={};
  for(const k of it.fields)settings[k]=fd.get(k)||'';
  await api('integrations/'+encodeURIComponent(kind),{method:'PUT',body:{provider:fd.get('provider'),settings}});
  closeModal();notify('تنظیمات ذخیره شد؛ سرویس تا زمان اتصال واقعی غیرفعال است');renderIntegrations();
 },{save:'ذخیره مشخصات'});
}
async function renderExpiryAlerts(){
 const days=Number($('#expiry-days')?.value||60);
 const d=await api('stock/expiry-alerts?days='+days+'&page='+state.page+'&limit=40');
 $('#page-content').innerHTML=`${head('هشدار تاریخ انقضا','مشاهده بچ‌هایی که تاریخ مصرفشان گذشته یا نزدیک است')}
 <div class="panel panel-padded" style="margin-bottom:16px"><div class="row wrap between">
 <div class="field" style="width:210px"><label>بازه هشدار</label>
 <select class="input" id="expiry-days">${[0,30,60,90,180,365,730].map(v=>`<option value="${v}" ${v===days?'selected':''}>${v===0?'منقضی‌شده':fa(v)+' روز آینده'}</option>`).join('')}</select></div>
 <button class="btn btn-outline" id="expiry-filter">اعمال فیلتر ${icon('check',16)}</button></div></div>
 <div class="panel"><div class="table-wrap"><table class="table"><thead><tr><th>کالا</th><th>بچ</th><th>انبار</th><th>موجودی</th><th>تاریخ انقضا</th><th>وضعیت</th></tr></thead>
 <tbody>${d.items.map(x=>`<tr><td>${esc(x.sku)}</td><td>${esc(x.lot)}</td><td>${esc(x.warehouse)}</td><td>${fa(x.quantity)}</td>
 <td>${dateFa(x.expiry_date)}</td><td>${x.days_left<0?'<span class="pill bad">منقضی‌شده</span>':`<span class="pill">${fa(x.days_left)} روز مانده</span>`}</td></tr>`).join('')||'<tr><td colspan="6">بچ دارای هشدار پیدا نشد.</td></tr>'}</tbody></table></div>
 <div class="pagination"><span>${fa(d.total)} هشدار</span><div class="row"><button class="btn btn-small btn-outline" id="expiry-prev" ${state.page<=1?'disabled':''}>قبلی</button>
 <button class="btn btn-small btn-outline" id="expiry-next" ${state.page*40>=d.total?'disabled':''}>بعدی</button></div></div></div>`;
}
async function renderAnalytics(){
 const now=new Date(), iso=d=>d.toISOString().slice(0,10);
 const end=$('#ana-end')?.value||iso(now);
 const start=$('#ana-start')?.value||iso(new Date(now.getTime()-89*86400000));
 const data=await api('analytics?start='+encodeURIComponent(start)+'&end='+encodeURIComponent(end));
 const vals=data.daily.slice(-35),max=Math.max(1,...vals.map(x=>x.sales));
 $('#page-content').innerHTML=`${head('تحلیل پیشرفته فروش','نمودار و شاخص‌های محاسبه‌شده از سفارش‌ها و ردیف‌های فروش')}
 <div class="panel panel-padded" style="margin-bottom:18px"><div class="row wrap between">
 <div class="row wrap"><div class="field"><label>از تاریخ</label><input class="input" id="ana-start" type="date" value="${esc(start)}"></div>
 <div class="field"><label>تا تاریخ</label><input class="input" id="ana-end" type="date" value="${esc(end)}"></div></div>
 <button class="btn btn-outline" id="analytics-refresh">به‌روزرسانی ${icon('check',16)}</button></div></div>
 <div class="metric-grid">
 ${[['مبلغ فروش',data.sales],['مبالغ وصول‌شده',data.paid],['میانگین سفارش',data.average_order],['تعداد سفارش',data.orders]].map(([k,v],i)=>`<div class="panel metric-card"><div class="label">${k}</div>
 <strong class="num">${i===3?fa(v):money(v)}</strong></div>`).join('')}</div>
 <div class="panel panel-padded" style="margin-top:18px"><div class="panel-title">روند فروش</div>
 ${vals.length?`<div class="bars">${vals.map(x=>`<div class="bar-item" title="${money(x.sales)}"><div class="bar" style="height:${Math.max(2,x.sales/max*90)}%"></div>
 <span class="bar-label">${dateFa(x.date).slice(0,5)}</span></div>`).join('')}</div>`:'<div class="empty">در این بازه سفارشی وجود ندارد</div>'}</div>
 <div class="dashboard-layout" style="margin-top:18px">
 <div class="panel panel-padded"><div class="panel-title">محبوب‌ترین کالاها</div>
 <div class="table-wrap"><table class="table"><thead><tr><th>SKU</th><th>تعداد</th><th>فروش</th><th>حاشیه ناخالص</th></tr></thead>
 <tbody>${data.top_products.map(x=>`<tr><td>${esc(x.sku)}</td><td>${fa(x.quantity)}</td><td>${money(x.sales)}</td><td>${money(x.gross_margin)}</td></tr>`).join('')}</tbody></table></div></div>
 <div class="panel panel-padded"><div class="panel-title">کانال‌های فروش</div>
 ${data.channels.map(x=>`<div class="recent-item between"><div><strong>${esc(x.channel)}</strong><div class="hint">${fa(x.orders)} سفارش</div></div><strong>${money(x.sales)}</strong></div>`).join('')||'بدون داده'}</div></div>`;
}

async function renderReports(){
 const report=await api('reports?type='+state.report);
 state.data.reportRows=report.rows;
 const cols=report.rows.length?Object.keys(report.rows[0]):[];
 $('#page-content').innerHTML=`${head('گزارش‌های مدیریتی','گزارش‌های متصل به سفارش‌ها، انبار و اسناد ثبت‌شده',`<button class="btn btn-primary" id="report-export" ${report.rows.length?'':'disabled'}>خروجی CSV ${icon('download',17)}</button>`)}<div class="panel"><div class="table-toolbar"><div class="filter-buttons">${REPORT_TYPES.map(([key,t])=>`<button type="button" data-report="${key}" class="filter-btn ${key===state.report?'active':''}">${t}</button>`).join('')}</div></div>${report.rows.length?`<div class="table-wrap" style="display:block"><table class="table"><thead><tr>${cols.map(k=>`<th>${esc(LABELS[k]||k)}</th>`).join('')}</tr></thead><tbody>${report.rows.map(x=>`<tr>${cols.map(k=>`<td>${val(k,x[k])}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`:'<div class="empty">برای این گزارش هنوز داده‌ای ثبت نشده است.</div>'}</div><p class="hint">در این نسخه گزارش‌ها تا ۱۰۰۰ رکورد آخر را نمایش می‌دهند. محاسبه سود، سود ناخالص بر مبنای بهای خرید زمان ثبت فروش است.</p>`;
}
function csvEscape(v){const str=String(v??'');return '"'+str.replaceAll('"','""')+'"'}
function exportCsv(){
 const rows=state.data.reportRows||[];if(!rows.length)return;
 const headers=Object.keys(rows[0]);const csv='\uFEFF'+[headers.map(h=>csvEscape(LABELS[h]||h)).join(','),...rows.map(x=>headers.map(h=>csvEscape(x[h])).join(','))].join('\r\n');
 const obj=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'}));
 const a=document.createElement('a');a.href=obj;a.download='ERP-'+state.report+'-'+new Date().toISOString().slice(0,10)+'.csv';a.click();setTimeout(()=>URL.revokeObjectURL(obj),1000);
}
async function renderSettings(){
 const [company,organizations]=await Promise.all([api('settings'),api('organizations')]);
 const owner=!state.me.public_demo&&['owner','admin'].includes(state.me.role);
 $('#page-content').innerHTML=`${head('تنظیمات کسب‌وکار','مشخصات فروشگاه و سازمان‌های قابل دسترسی')}<div class="dashboard-layout"><section class="panel panel-padded"><div class="panel-title">اطلاعات شرکت</div><div class="panel-sub">این اطلاعات مربوط به سازمان جاری است.</div><form id="settings-form" class="stack" style="margin-top:20px"><div class="field"><label>نام کسب‌وکار</label><input class="input" name="name" required maxlength="200" value="${esc(company.name)}" ${owner?'':'disabled'}></div><div class="field"><label>شماره تماس</label><input class="input" name="phone" value="${esc(company.phone||'')}" ${owner?'':'disabled'}></div><div class="field"><label>نشانی</label><textarea class="input" name="address" rows="3" ${owner?'':'disabled'}>${esc(company.address||'')}</textarea></div><div class="notice">واحد پول ذخیره‌شده: تومان. مقادیر مالی در دیتابیس به‌صورت عدد صحیح ذخیره می‌شوند.</div>${owner?`<button class="btn btn-primary" type="submit" style="align-self:flex-start">ذخیره تنظیمات ${icon('check',16)}</button>`:''}</form></section><section class="panel panel-padded"><div class="panel-title">سازمان‌های من</div><div class="panel-sub">تغییر سازمان فقط با عضویت فعال امکان‌پذیر است.</div><div class="stack" style="margin-top:15px">${organizations.items.map(t=>`<div class="alert-row between"><div><div class="strong">${esc(t.name)}</div><div class="hint">${esc(t.role)}</div></div>${t.id===state.me.tenant_id?'<span class="pill good">فعال</span>':`<button class="btn btn-small btn-light" data-switch-org="${t.id}">انتخاب</button>`}</div>`).join('')}</div></section></div>`;
}
async function renderTeam(){
 if(!['owner','admin'].includes(state.me.role)){
  $('#page-content').innerHTML=`${head('کاربران و دسترسی')}<div class="panel empty">تنها مالک و مدیر سازمان به مدیریت کاربران دسترسی دارند.</div>`;return;
 }
 const result=await api('members');state.data.members=result.items;
 $('#page-content').innerHTML=`${head('اعضای کسب‌وکار','مدیریت حساب‌ها و سطح دسترسی به اطلاعات',`${state.me.public_demo?'':`<button class="btn btn-primary" id="invite-user">دعوت عضو جدید ${icon('plus',16)}</button>`}`)}<div class="panel"><div class="table-wrap" style="display:block"><table class="table"><thead><tr><th>نام</th><th>ایمیل</th><th>نقش</th><th>وضعیت</th><th>عملیات</th></tr></thead><tbody>${result.items.map(m=>`<tr><td>${esc(m.name)}</td><td dir="ltr">${esc(m.email)}</td><td>${esc(m.role)}</td><td>${m.active?'<span class="pill good">فعال</span>':'<span class="pill bad">غیرفعال</span>'}</td><td>${!state.me.public_demo&&m.id&&m.email!==state.me.email?`<button class="btn btn-small btn-light" data-team-edit="${m.id}">تغییر سطح دسترسی ${icon('edit',15)}</button>`:'<span class="muted">فقط مشاهده</span>'}</td></tr>`).join('')}</tbody></table></div></div><p class="hint">دعوت‌نامه برای کاربران ثبت‌نام‌شده قابل پذیرش است. ارسال ایمیل خودکار هنوز متصل نیست؛ لینک دعوت را دستی به عضو جدید بدهید.</p>`;
}
function openInvite(){
 showModal('دعوت عضو جدید',`<div class="form-grid"><div class="field full"><label>ایمیل عضو</label><input class="input" name="email" type="email" placeholder="person@example.com" required dir="ltr"></div><div class="field full"><label>سطح دسترسی</label>${selectField('role',OPTIONS.role.map(([id,label])=>({id,label})))}</div></div><p class="hint">لینک دعوت ۷ روز اعتبار دارد. عضو باید با همین ایمیل وارد پنل شده باشد.</p>`,async form=>{
  const f=new FormData(form);const r=await api('invites',{method:'POST',body:{email:f.get('email'),role:f.get('role')}});
  const link=location.origin+'/?invite='+encodeURIComponent(r.token);
  showModal('لینک دعوت ایجاد شد',`<div class="notice">لینک را فقط برای ایمیل ${esc(r.email)} ارسال کنید.</div><div class="field" style="margin-top:20px"><label>لینک دعوت</label><textarea readonly class="input" rows="3" id="invite-link" dir="ltr">${esc(link)}</textarea></div><button class="btn btn-light" type="button" id="copy-invite" style="margin-top:13px">کپی لینک</button>`,async()=>{closeModal()},{save:'بستن'});
 },{save:'ایجاد دعوت‌نامه'});
}
function openMemberEdit(id){
 const obj=(state.data.members||[]).find(m=>m.id===id);if(!obj)return;
 showModal('تغییر دسترسی '+obj.name,`<div class="form-grid"><div class="field"><label>نقش</label>${selectField('role',OPTIONS.role.map(([id,label])=>({id,label})),obj.role)}</div><div class="field"><label>وضعیت</label>${selectField('active',[{id:'true',label:'فعال'},{id:'false',label:'غیرفعال'}],String(obj.active))}</div></div>`,async form=>{
  const f=new FormData(form);
  await api('members/'+id,{method:'PATCH',body:{role:f.get('role'),active:f.get('active')==='true'}});
  closeModal();notify('دسترسی کاربر به‌روزرسانی شد');loadView();
 });
}
async function maybeAcceptInvite(){
 const token=new URL(location.href).searchParams.get('invite');if(!token)return;
 try{await api('auth/accept-invite',{method:'POST',body:{token}});state.me=await api('auth/me');notify('عضویت جدید فعال شد')}catch(e){notify('پذیرش دعوت انجام نشد: '+e.message,true)}
 history.replaceState(null,'',location.pathname+'#dashboard');
}
root.addEventListener('click',async e=>{
 const btn=e.target.closest('button');if(!btn)return;
 try{
 if(btn.hasAttribute('data-auth-tab'))return renderAuth(btn.dataset.authTab);
 if(btn.hasAttribute('data-nav'))return setView(btn.dataset.nav);
 if(btn.id==='menu-toggle'){state.menu=!state.menu;$('#shell')?.classList.toggle('menu-open',state.menu);return}
 if(btn.id==='logout'){await api('auth/logout',{method:'POST'});renderAuth();notify('از حساب خارج شدید');return}
 if(btn.id==='notif-toggle'){state.notifOpen=!state.notifOpen;$('#notif-pop')?.classList.toggle('hide',!state.notifOpen);return}
 if(btn.id==='retry-view')return loadView();
 if(btn.hasAttribute('data-demo-workflow'))return openDemoWorkflow(btn.dataset.demoWorkflow);
 if(btn.id==='new-record'){
  if(state.view==='transfers')return openTransfer();
  if(state.view==='purchases'||state.view==='sales')return openDocument(state.view);
  return openGeneric(state.view);
 }
 if(btn.id==='analytics-refresh')return renderAnalytics();
 if(btn.hasAttribute('data-revoke-session')){if(confirm('نشست انتخاب‌شده لغو شود؟')){await api('auth/sessions/'+btn.dataset.revokeSession+'/revoke',{method:'POST',body:{}});notify('نشست لغو شد');return renderSecurity()}}
 if(btn.id==='security-change-password')return openChangePassword();
 if(btn.id==='expiry-filter')return renderExpiryAlerts();
 if(btn.id==='expiry-prev'){state.page=Math.max(1,state.page-1);return renderExpiryAlerts()}
 if(btn.id==='expiry-next'){state.page++;return renderExpiryAlerts()}
 if(btn.hasAttribute('data-configure-integration'))return openConfigureIntegration(btn.dataset.configureIntegration);
 if(btn.hasAttribute('data-partial-fulfill'))return openPartialFulfill(btn.dataset.partialFulfill);
 if(btn.hasAttribute('data-fulfillment-details'))return openFulfillmentDetails(btn.dataset.fulfillmentDetails);
 if(btn.id==='fulfill-prev'){state.page=Math.max(1,state.page-1);return renderFulfillments()}
 if(btn.id==='fulfill-next'){state.page++;return renderFulfillments()}
 if(btn.id==='ledger-new-account')return openLedgerAccount();
 if(btn.id==='ledger-setup'){await api('ledger/bootstrap',{method:'POST',body:{}});notify('حساب‌ها ایجاد شدند');return renderLedger()}
 if(btn.id==='ledger-new-journal')return openLedgerJournal();
 if(btn.hasAttribute('data-journal-detail'))return openLedgerDetails(btn.dataset.journalDetail);
 if(btn.id==='ledger-prev'){state.page=Math.max(1,state.page-1);return renderLedger()}
 if(btn.id==='ledger-next'){state.page++;return renderLedger()}
 if(btn.id==='issue-invoice')return openIssueInvoice();
 if(btn.id==='invoice-prev'){state.page=Math.max(1,state.page-1);return renderInvoices()}
 if(btn.id==='invoice-next'){state.page++;return renderInvoices()}
 if(btn.id==='register-serials')return openRegisterSerials();
 if(btn.id==='adjust-stock')return openAdjustment();
 if(btn.id==='count-refresh')return renderCycleCount();
 if(btn.id==='count-prev'){state.page=Math.max(1,state.page-1);return renderCycleCount()}
 if(btn.id==='count-next'){state.page++;return renderCycleCount()}
 if(btn.id==='page-prev'){state.page=Math.max(1,state.page-1);return loadView()}
 if(btn.id==='page-next'){state.page++;return loadView()}
 if(btn.hasAttribute('data-edit')){const [resource,id]=btn.dataset.edit.split(':');return openGeneric(resource,id)}
 if(btn.hasAttribute('data-delete')){
  const [resource,id]=btn.dataset.delete.split(':');
  if(!confirm('آیا از حذف یا غیرفعال‌کردن این رکورد مطمئن هستید؟'))return;
  await api(`data/${resource}/${id}`,{method:'DELETE'});notify('عملیات با موفقیت انجام شد');return loadView();
 }
 if(btn.hasAttribute('data-workflow')){
  const [resource,id,action]=btn.dataset.workflow.split(':');
  if(resource==='purchases'&&action==='receive')return openReceivePurchase(id);
  if(!confirm('این عملیات موجودی یا وضعیت سند را تغییر می‌دهد. ادامه می‌دهید؟'))return;
  await api(`${resource}/${id}/${action}`,{method:'POST',body:resource==='purchases'?{idempotency_key:uid()}:{} });notify('وضعیت ثبت شد');return loadView();
 }
 if(btn.hasAttribute('data-return-settle'))return openReturnSettlement(btn.dataset.returnSettle);
 if(btn.hasAttribute('data-document-action')){
  const [kind,id]=btn.dataset.documentAction.split(':');
  if(kind.startsWith('pay-'))return openPayment(kind.slice(4),id);
  if(kind.endsWith('-return'))return openReturn(kind.split('-')[0],id);
 }
 if(btn.hasAttribute('data-mark-read')){await api(`notifications/${btn.dataset.markRead}/read`,{method:'POST',body:{}});await refreshNotifs();if(state.view==='notifications')loadView();return}
 if(btn.hasAttribute('data-report')){state.report=btn.dataset.report;return renderReports()}
 if(btn.id==='report-export')return exportCsv();
 if(btn.id==='invite-user')return openInvite();
 if(btn.hasAttribute('data-team-edit'))return openMemberEdit(btn.dataset.teamEdit);
 if(btn.hasAttribute('data-switch-org')){
  await api('organizations/switch',{method:'POST',body:{tenant_id:btn.dataset.switchOrg}});
  state.me=await api('auth/me');state.lookups={};renderShell();setView('dashboard');return;
 }
 }catch(err){notify(err.message,true)}
});
root.addEventListener('submit',async e=>{
 if(e.target.id==='cycle-count-form'){
  e.preventDefault();
  const form=e.target,btn=$('#cycle-submit');
  const warehouse_id=$('#cycle-warehouse')?.value;
  const items=$('.count-row',form).map(row=>({
   variant_id:row.dataset.variant,
   expected_quantity:Number(row.dataset.expected),
   counted:Number(row.querySelector('input[name=counted]').value)
  }));
  if(!items.length)return notify('قلمی برای شمارش وجود ندارد',true);
  if(items.some(x=>!Number.isSafeInteger(x.counted)||x.counted<0))return notify('تعداد واردشده نامعتبر است',true);
  if(!confirm('انبارگردانی ثبت شود؟ اختلاف‌ها موجودی و دفتر گردش را تغییر می‌دهند.'))return;
  btn.disabled=true;
  try{
   const r=await api('stock/cycle-count',{method:'POST',body:{warehouse_id,items,idempotency_key:uid()}});
   notify('انبارگردانی ثبت شد. '+fa(r.items.filter(x=>x.difference!==0).length)+' قلم اصلاح شد');
   await renderCycleCount(warehouse_id);
  }catch(err){notify(err.message,true);btn.disabled=false}
  return;
 }
 if(e.target.id==='auth-form'){
  e.preventDefault();const form=e.target,mode=form.dataset.mode,f=new FormData(form),btn=$('button[type=submit]',form);
  const body=mode==='register'?{name:f.get('name'),company:f.get('company'),email:f.get('email'),password:f.get('password')}:{email:f.get('email'),password:f.get('password')};
  btn.disabled=true;try{await api('auth/'+mode,{method:'POST',body});state.me=await api('auth/me');await maybeAcceptInvite();state.lookups={};renderShell();setView('dashboard');notify('خوش آمدید')}catch(err){notify(err.message,true);btn.disabled=false}
 }
 if(e.target.id==='settings-form'){
  e.preventDefault();const f=new FormData(e.target);
  try{await api('settings',{method:'PATCH',body:{name:f.get('name'),phone:f.get('phone'),address:f.get('address')}});state.me=await api('auth/me');renderShell();setView('settings');notify('تنظیمات ذخیره شد')}catch(err){notify(err.message,true)}
 }
});
root.addEventListener('change',e=>{if(e.target.id==='cycle-warehouse'){state.page=1;renderCycleCount(e.target.value)}});
root.addEventListener('input',e=>{
 if(e.target.id==='table-search'){
  const term=e.target.value;clearTimeout(window.__erpSearch);
  window.__erpSearch=setTimeout(()=>{state.search=term;state.page=1;loadView();const el=$('#table-search');if(el){el.focus();el.setSelectionRange(el.value.length,el.value.length)}},450);
 }
});
root.addEventListener('click',e=>{if(e.target.id==='menu-shade'){state.menu=false;$('#shell').classList.remove('menu-open')}});
modals.addEventListener('click',e=>{
 if(e.target.id==='overlay'||e.target.closest('#modal-close')||e.target.closest('#modal-cancel'))return closeModal();
 if(e.target.closest('#copy-invite')){
  const el=$('#invite-link');navigator.clipboard?.writeText(el.value).then(()=>notify('لینک کپی شد')).catch(()=>{el.select();notify('لینک انتخاب شد؛ آن را کپی کنید')});
 }
});
modals.addEventListener('submit',async e=>{
 if(e.target.id!=='modal-form')return;
 e.preventDefault();const fn=modalSubmit,btn=$('#modal-save');if(!fn)return;
 btn.disabled=true;
 try{await fn(e.target)}catch(err){notify(err.message,true);if(btn?.isConnected)btn.disabled=false}
});
window.addEventListener('keydown',e=>{if(e.key==='Escape'&&modals.innerHTML)closeModal()});
function renderShowroomUnavailable(){
 state.me=null;
 root.innerHTML=`<main class="auth-layout" dir="rtl"><section class="auth-form-area"><div class="auth-form" role="alert">
 <div class="auth-logo"><span class="logo-symbol">◈</span> ERP فروشگاهی</div>
 <h2>در حال اتصال به نسخه نمایشی</h2>
 <p class="subtitle">پنل برای بازدید عمومی بدون ورود تنظیم شده است. در حال حاضر داده‌های دمو دریافت نشدند؛ اتصال را دوباره بررسی کنید.</p>
 <button type="button" class="btn btn-primary" id="demo-retry">تلاش دوباره ${icon('swap',17)}</button>
 </div></section></main>`;
}
root.addEventListener('click',e=>{if(e.target.closest('#demo-retry'))window.location.reload()});
async function boot(){
 try{
  state.me=await api('auth/me');
  await maybeAcceptInvite();
  renderShell();
  const hash=location.hash.slice(1);
  state.view=(hash==='dashboard'||META[hash]||['reports','settings','team','cycle-count','invoices','ledger-accounts','ledger-journals','ledger-balance','ledger-profit','analytics','expiry-alerts','integrations','security','fulfillments'].includes(hash))?hash:'dashboard';
  setView(state.view);
 }catch{
  // An unavailable demo must never accidentally expose the normal login
  // form to someone visiting the public showroom.
  try{
   const status=await fetch('/api/public-mode',{cache:'no-store'});
   if(status.ok){
    const mode=await status.json();
    if(!mode.enabled){renderAuth();return}
   }
  }catch{}
  renderShowroomUnavailable();
 }
}
boot();