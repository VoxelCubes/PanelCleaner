# پنل کلینر (Panel Cleaner)

[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/voxelcubes/PanelCleaner?logo=GitHub)](https://github.com/voxelcubes/PanelCleaner/releases)
[![PyPI version](https://img.shields.io/pypi/v/pcleaner)](https://pypi.org/project/pcleaner/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Crowdin](https://badges.crowdin.net/panel-cleaner/localized.svg)](https://crowdin.com/project/panel-cleaner)

> **فهرست**
>
> [ویژگی‌ها](#ویژگی‌ها) \
> [محدودیت‌ها](#محدودیت‌ها) \
> [چرا از این برنامه استفاده کنیم؟](#چرا-از-این-برنامه-استفاده-کنیم) \
> [نصب](#نصب) \
> [استفاده](#استفاده) \
> [پروفایل‌ها](#پروفایل‌ها) \
> [OCR](#ocr) \
> [OCR هوشمند (اصلاح با LLM)](#ocr-هوشمند-اصلاح-با-llm) \
> [نمونه‌ها](#نمونه‌هایی-از-حباب‌های-پیچیده) \
> [تشکر و قدردانی](#تشکر-و-قدردانی) \
> [پروانه](#پروانه) \
> [نقشه راه](#نقشه-راه) \
> [سؤالات متداول](https://github.com/VoxelCubes/PanelCleaner/blob/master/docs/faq.md) \
> [ترجمه](https://github.com/VoxelCubes/PanelCleaner/blob/master/translations/TRANSLATING.md)

---

این ابزار با استفاده از یادگیری ماشین، متن را پیدا کرده و سپس با بالاترین دقت ممکن، ماسک‌هایی برای پوشاندن آن تولید می‌کند. هدف آن پاک کردن حباب‌های ساده است؛ هیچ عملیات inpainting یا حذفِ متنِ خارج از حباب انجام نمی‌شود. این برنامه طراحی شده تا حجم زیادی از کارهای تکراری را برای افرادی که باید پنل‌های زیادی را پاک کنند، کاهش دهد، ضمن اینکه مطمئن شود چیزی را که نباید پاک کند، پوشش نمی‌دهد.

![نمونه](https://raw.githubusercontent.com/VoxelCubes/PanelCleaner/master/media/spread.png)

![نمونه](https://raw.githubusercontent.com/VoxelCubes/PanelCleaner/master/media/screenshots/cleaning_done.png)

![نمونه](https://raw.githubusercontent.com/VoxelCubes/PanelCleaner/master/media/screenshots/details.png)

تصویر بالا (صفحه بالا-راست) نشان می‌دهد:

- جعبه‌های مختلفی در جایی که هوش مصنوعی متن پیدا کرده رسم شده است.

- (سبز) هوش مصنوعی همچنین یک ماسک دقیق در جایی که متن را تشخیص داده، تولید می‌کند.

- (بنفش) این ماسک‌ها بسط داده شده‌اند تا هر متن مجاوری که تشخیص داده نشده و همچنین artifacts مربوط به فشرده‌سازی jpeg را پوشش دهند.

- (آبی) برای ماسک‌هایی که تنگ هستند، حاشیه اطراف لبه ماسک برای پاک‌سازی نهایی نویزگیری می‌شود، بدون اینکه بقیه تصویر تحت تأثیر قرار گیرد.

دو صفحه پایین، خروجی‌های برنامه هستند: یا فقط لایه ماسک شفاف و/یا ماسک اعمال‌شده روی تصویر اصلی که آن را پاک می‌کند.

---

## ویژگی‌ها

- حباب‌های متنی را بدون برجای گذاشتن artifact پاک می‌کند.

- از پوشش دادن بخش‌هایی از تصویر که متن نیستند، اجتناب می‌کند.

- حباب‌هایی که نمی‌توان با ماسک پوشاند را (با LaMa و یادگیری ماشین) inpaint می‌کند.

- حباب‌هایی که فقط شامل نمادها یا اعداد هستند را نادیده می‌گیرد، زیرا نیازی به ترجمه ندارند.

- یک رابط گرافیکی (GUI) برای استفاده آسان ارائه می‌دهد؛ تم‌های تاریک، روشن و سیستمی پشتیبانی می‌شوند.

- پس از نصب داده‌های مدل، به اتصال اینترنت نیاز ندارد.

- مجموعه‌ای گسترده از گزینه‌ها برای سفارشی‌سازی فرآیند پاک‌سازی و امکان ذخیره چندین پیش‌تنظیم به‌عنوان پروفایل را ارائه می‌دهد.
  برای مشاهده فهرست تمام گزینه‌ها، [پروفایل پیش‌فرض](https://github.com/VoxelCubes/PanelCleaner/blob/master/media/default.conf) را ببینید.

- تحلیل‌های دقیقی از فرآیند پاک‌سازی ارائه می‌دهد تا ببینید تنظیماتتان چه تأثیری روی نتایج دارند.

- در صورتی که به‌صورت بسته پایتون نصب شود و سخت‌افزار شما پشتیبانی کند، از شتاب‌دهی CUDA بهره می‌برد.

- از پردازش دسته‌ای (batch) تصاویر و پوشه‌ها پشتیبانی می‌کند.

- می‌تواند با حباب‌هایی روی هر رنگ پس‌زمینه یکدست کار کند.

- می‌تواند متن را از بقیه تصویر برش دهد، مثلاً برای جایگذاری روی یک نسخه رنگی.

- می‌تواند روی صفحات OCR اجرا کند و متن را در یک فایل ذخیره کند.

- به‌صورت اختیاری خروجی OCR را از طریق یک مدل زبانی بزرگ (با [airllm](https://github.com/lyogavin/Anima/tree/main/air_llm)) عبور می‌دهد تا متن‌های نامفهوم را اصلاح کند — «اصلاح هوشمند OCR».

- مرور خروجی پاک‌سازی و OCR، از جمله ویرایش تعاملی خروجی OCR پیش از ذخیره آن.

- رابط کاربری به زبان‌های: انگلیسی، آلمانی، بلغاری، اسپانیایی
  (برای زبان‌های بیشتر به [ترجمه](https://github.com/VoxelCubes/PanelCleaner/blob/master/translations/TRANSLATING.md) مراجعه کنید)

---

## محدودیت‌ها

- برای پاک‌سازی فقط از متن ژاپنی و انگلیسی پشتیبانی می‌کند (موفقیت با زبان‌های دیگر ممکن است متفاوت باشد)؛ برای OCR فقط ژاپنی.

- انواع فایل پشتیبانی‌شده: ‎.jpeg، ‎.jpg، ‎.png، ‎.bmp، ‎.tiff، ‎.tif، ‎.jp2، ‎.dib، ‎.webp، ‎.ppm
- انواع فایل پشتیبانی‌شده (فقط خروجی): ‎.psd

- برنامه برای تشخیص اولیه متن به هوش مصنوعی تکیه می‌کند که ذاتاً بی‌نقص نیست. گاهی ممکن است بخش‌های کوچکی از متن را از قلم بیندازد یا بخشی از حباب را به‌اشتباه به‌عنوان متن تشخیص دهد که مانع پاک‌سازی آن حباب می‌شود. از آزمایش‌ها، این معمولاً بین ۲ تا ۸ درصد حباب‌ها را بسته به تنظیمات شما تحت تأثیر قرار می‌دهد.

- به دلیل رویکرد محافظه‌کارانه در انتخاب ماسک‌ها، اگر برنامه نتواند حباب را با رضایت‌بخشی پاک کند، آن حباب را رها می‌کند. البته این امر از مثبت کاذب (false positive) نیز جلوگیری می‌کند.

- برای ماسک‌ها، در حال حاضر فقط مقیاس خاکستری (grayscale) پشتیبانی می‌شود. یعنی می‌تواند متن را در حباب‌های سفید، سیاه یا خاکستری پوشش دهد، اما نه حباب‌های رنگی.

---

## چرا از این برنامه استفاده کنیم؟

این برنامه برای پاک‌سازی دقیق و کامل حباب‌های متنی طراحی شده، بدون اینکه artifact‌ای برجای بگذارد.
هدف آن صرفه‌جویی در زمان پاک‌کننده‌ها و انجام کارهای تکراری است.
[هوش مصنوعی](https://github.com/dmMaze/comic-text-detector) که برای تشخیص متن و تولید ماسک اولیه استفاده شده، بخشی از این پروژه *نیست*؛ این پروژه فقط از آن به‌عنوان نقطه شروع استفاده کرده و خروجی‌اش را بهبود می‌بخشد.

| تصویر اصلی                          | خروجی هوش مصنوعی                    | پنل کلینر                            |
|:-----------------------------------:|:-----------------------------------:|:------------------------------------:|
| ![Original](https://raw.githubusercontent.com/VoxelCubes/PanelCleaner/master/media/demo_original.png) | ![AI Output](https://raw.githubusercontent.com/VoxelCubes/PanelCleaner/master/media/demo_ai_raw.png) | ![Panel Cleaner](https://raw.githubusercontent.com/VoxelCubes/PanelCleaner/master/media/demo_clean.png) |

همان‌طور که می‌بینید، با کمی پاک‌سازی اضافی روی خروجی هوش مصنوعی، مقداری متن باقی‌مانده و artifact‌های فشرده‌سازی jpeg حذف می‌شوند و حباب کاملاً پاک می‌شود. \
وقتی پاک‌سازی کامل ممکن نباشد، پنل کلینر آن حباب را رها می‌کند تا وقت شما با یک پاک‌سازی نامناسب هدر نرود. رفتار دقیق پاک‌سازی به‌شدت قابل تنظیم است؛ برای جزئیات بیشتر به [پروفایل‌ها](#پروفایل‌ها) مراجعه کنید.

---

## نصب

می‌توانید بین نصب یک باینری از پیش ساخته‌شده (exe یا elf) از [بخش انتشارها](https://github.com/VoxelCubes/PanelCleaner/releases/latest) (**توصیه‌شده برای اغلب کاربران**)، یا نصب روی مفسر پایتون محلی خود با pip، یکی را انتخاب کنید.

توجه: همه نسخه‌ها در اولین اجرا نیاز به دانلود داده‌های مدل دارند (حدود ۵۰۰ مگابایت). این داده‌های مدل در صورت به‌روزرسانی پنل کلینر نیازی به دانلود مجدد ندارند.

مهم: باینری‌های از پیش ساخته‌شده از شتاب‌دهی CUDA پشتیبانی نمی‌کنند. برای استفاده از CUDA، باید برنامه را با pip نصب کنید و نسخه مناسب [pytorch](https://pytorch.org/get-started/locally/) را برای سیستم خود نصب کنید.

### نصب با Pip

برنامه به **پایتون ۳.۱۰ یا جدیدتر** نیاز دارد.

برنامه را با هم رابط خط فرمان و رابط گرافیکی با pip از [PyPI](https://pypi.org/project/pcleaner/) نصب کنید:
```bash
pip install pcleaner
```

یا اگر فقط می‌خواهید از رابط خط فرمان استفاده کنید:
```bash
pip install pcleaner-cli
```
توجه: `pcleaner` و `pcleaner-cli` می‌توانند در کنار هم نصب شوند، اما بسته فقط-خط‌فرمان افزاینده خواهد بود.

توجه: آزمایش شده که برنامه روی لینوکس، مک‌اواس و ویندوز با سطوح مختلفی از تنظیمات اولیه کار می‌کند. برای راهنمایی به [سؤالات متداول](https://github.com/VoxelCubes/PanelCleaner/blob/master/docs/faq.md) مراجعه کنید.

### نصب از AUR (آرچ لینوکس)

این روش برنامه را در یک محیط `pipx` نصب می‌کند که به pytorch اجازه می‌دهد نسخه مناسب CUDA را برای سیستم شما دانلود کند؛ بنابراین بهترین روش نصب است.

می‌توانید بسته را این‌جا پیدا کنید: [panelcleaner](https://aur.archlinux.org/packages/panelcleaner)

این دستور `pcleaner` و `pcleaner-gui` را همراه با یک فایل دسکتاپ برای GUI فراهم می‌کند.

با helper مورد علاقه AUR خود نصب کنید، مثلاً با `yay`:
```bash
yay -S panelcleaner
```

### نصب با Flatpak

این روش باینری از پیش ساخته‌شده را در یک کانتینر flatpak نصب می‌کند که از شتاب‌دهی CUDA پشتیبانی نمی‌کند.

[دریافت از Flathub](https://flathub.org/apps/io.github.voxelcubes.panelcleaner)

### نصب با Docker

تصویر را با buildx بسازید:
```bash
docker buildx build -t pcleaner:v1 .
```
یا با builder قدیمی:
```bash
docker image build -t pcleaner:v1 .
```

سپس تصویر داکر را با تعیین یک پوشه ریشه برای دسترسی کانتینر راه‌اندازی کنید.
در این مثال، پوشه جاری (`pwd`) استفاده شده است:
```bash
docker run -it --name pcleaner -v $(pwd):/app pcleaner:v1
```
این کار همچنین یک شل تعاملی در کانتینر باز می‌کند.

بعداً می‌توانید با این دستور یکی دیگر باز کنید:
```bash
docker start pcleaner
docker exec -it pcleaner bash
```

---

## استفاده

برنامه از خط فرمان قابل اجراست و در رایج‌ترین حالت، هر تعداد تصویر یا پوشه را به‌عنوان ورودی می‌پذیرد. برنامه یک پوشه جدید به نام `cleaned` در همان پوشه فایل‌های ورودی می‌سازد و تصاویر و/یا ماسک‌های پاک‌شده را آن‌جا قرار می‌دهد. اغلب مفیدتر است که فقط لایه ماسک را خروجی بگیرید، که می‌توانید با اضافه کردن گزینه `--save-only-mask` یا به‌اختصار `-m` این کار را انجام دهید.

نمونه‌ها:
```bash
pcleaner clean image1.png image2.png image3.png

pcleaner clean -m folder1 image1.png
```

نمایش با ۴۶ تصویر، در زمان واقعی، با شتاب‌دهی CUDA.
![نمایش](https://raw.githubusercontent.com/VoxelCubes/PanelCleaner/master/media/pcleaner_demo.gif)

گزینه‌های بسیار بیشتری وجود دارد که با اجرای دستور زیر قابل مشاهده است:
```bash
pcleaner --help
```

### راه‌اندازی GUI با خط فرمان

GUI با دستور `gui` از خط فرمان قابل راه‌اندازی است:
```bash
pcleaner gui
```
یا مستقیماً با
```bash
pcleaner-gui
```

اگر pcleaner پیدا نمی‌شود، مطمئن شوید در متغیر PATH شماست، یا این را امتحان کنید:
```bash
python -m pcleaner
```

---

## پروفایل‌ها

برنامه هر تنظیم ممکن را در یک پروفایل پیکربندی که به‌صورت فایل‌های متنی ساده ذخیره می‌شوند و از طریق GUI نیز قابل دسترسی هستند، expos می‌کند. هر گزینه پیکربندی در خود فایل توضیح داده شده و به شما اجازه می‌دهد هر پارامتر فرآیند پاک‌سازی را برای نیازهای خاص خود بهینه کنید. \
کافی است یک پروفایل جدید بسازید:
```bash
pcleaner profile new my_profile_name_here
```

و پروفایل جدیدتان در یک ویرایشگر متن برایتان باز می‌شود. \
در اینجا یک قطعه کوچک از پروفایل پیش‌فرض آمده است:
```ini
# Number of pixels to grow the mask by each step. 
# This bulks up the outline of the mask, so smaller values will be more accurate but slower.
mask_growth_step_pixels = 2

# Number of steps to grow the mask by.
# A higher number will make more and larger masks, ultimately limited by the reference box size.
mask_growth_steps = 11
```

با اضافه کردن `--profile=my_profile_name_here` یا
`-p my_profile_name_here` به دستور، کلینر را با پروفایل مشخص‌شده اجرا کنید.

اگر در دیدن اینکه تنظیمات چه تأثیری روی نتایج دارند مشکل دارید، می‌توانید از
گزینه `--cache-masks` برای ذخیره تصویرسازی مراحل میانی در پوشه کش استفاده کنید.

| پروفایل پیش‌فرض                                | پروفایل سفارشی                              |
| ---------------------------------------------- | ------------------------------------------- |
| ![Default Profile](https://raw.githubusercontent.com/VoxelCubes/PanelCleaner/master/media/profile_original.png) | ![Custom Profile](https://raw.githubusercontent.com/VoxelCubes/PanelCleaner/master/media/profile_modded.png) |
| mask_growth_step_pixels = 2                    | mask_growth_step_pixels = 4                 |
| mask_growth_steps = 11                         | mask_growth_steps = 4                       |

علاوه بر این، برای هر مرحله پردازش در ترمینال تحلیل‌هایی ارائه می‌شود تا ببینید تنظیماتتان در مجموع چه تأثیری روی نتایج دارند.

برای فهرست تمام گزینه‌ها، [پروفایل پیش‌فرض](https://github.com/VoxelCubes/PanelCleaner/blob/master/media/default.conf) را ببینید.

توجه: پروفایل پیش‌فرض برای تصاویری با ابعاد تقریبی ۱۱۰۰×۱۶۰۰ پیکسل بهینه شده است.
اگر از تصاویر با وضوح به‌مراتب کمتر یا بیشتر استفاده می‌کنید، پارامترهای ابعاد را در یک پروفایل متناسب تنظیم کنید.

پیش از خروجی گرفتن از تصاویر پاک‌شده، تنظیماتتان را با چند حالت نمایش مرور کنید.
![مرور](https://raw.githubusercontent.com/VoxelCubes/PanelCleaner/master/flatpak/Screenshot_review.png)

---

## OCR

همچنین می‌توانید از پنل کلینر برای انجام تشخیص کاراکتر نوری (OCR) روی صفحات استفاده کنید
و متن را در یک فایل ذخیره کنید. این می‌تواند برای کمک به ترجمه یا استخراج متن برای اهداف تحلیلی مفید باشد. \
می‌توانید OCR را با این دستور اجرا کنید:
```bash
pcleaner ocr myfolder --output-path=output.txt
```

پنل کلینر برای OCR ژاپنی به‌صورت پیش‌فرض از [MangaOCR](https://github.com/kha-white/manga-ocr) استفاده می‌کند که روش ترجیحی برای OCR متن ژاپنی است.
در صورت موجود بودن، پنل کلینر می‌تواند از Tesseract نیز برای OCR استفاده کند، به‌ویژه برای پردازش متن انگلیسی و
ژاپنی — تنها دو زبانی که در حال حاضر پشتیبانی می‌شوند.

این قابلیت در GUI نیز به‌عنوان گزینه خروجی OCR موجود است.
همچنین می‌توانید خروجی OCR را آن‌جا به‌صورت تعاملی مرور و ویرایش کنید.
![مرور](https://raw.githubusercontent.com/VoxelCubes/PanelCleaner/master/flatpak/Screenshot_ocr.png)

برای نصب Tesseract روی سیستم خود، دستورالعمل‌های زیر را دنبال کنید.

### نصب Tesseract

#### ویندوز

1. نصب‌کننده را از [مخزن رسمی GitHub تی Tesseract](https://github.com/tesseract-ocr/tessdoc?tab=readme-ov-file#releases-and-changelog) دانلود کنید.
توصیه می‌شود آخرین نسخه از UB Mannheim لینک‌شده را دریافت کنید (۶۴ بیت).
2. نصب‌کننده را اجرا کنید و دستورالعمل‌های روی صفحه را برای نصب سیستم‌کلی دنبال کنید.
3. پوشه نصب Tesseract را به متغیر محیطی PATH خود اضافه کنید.
اگر نصب سیستم‌کلی انجام داده‌اید، این یعنی اضافه کردن پوشه `C:\Program Files\Tesseract-OCR` [به PATH خود](https://www.computerhope.com/issues/ch000549.htm).
4. رایانه خود را راه‌اندازی مجدد کنید.

#### مک‌اواس

از Homebrew برای نصب Tesseract استفاده کنید:

```bash
brew install tesseract
```

#### لینوکس

برای توزیع‌های مبتنی بر دبیان، از apt استفاده کنید:

```bash
sudo apt install tesseract-ocr
```

برای سایر توزیع‌ها، به package manager خود و [مستندات رسمی Tesseract](https://tesseract-ocr.github.io/tessdoc/Home.html) مراجعه کنید.

برای دستورالعمل‌های نصب دقیق و اطلاعات بیشتر، لطفاً به [مستندات رسمی Tesseract](https://tesseract-ocr.github.io/tessdoc/) مراجعه کنید.

> توجه: اگرچه Tesseract از زبان‌های اضافی پشتیبانی می‌کند، پنل کلینر فقط از Tesseract برای تشخیص متن انگلیسی و ژاپنی استفاده می‌کند. انگلیسی به‌صورت پیش‌فرض نصب است. برای نصب بسته زبان ژاپنی، دستورالعمل‌های [نصب بسته‌های زبان اضافی](https://ocrmypdf.readthedocs.io/en/latest/languages.html) را دنبال کنید.

---

## OCR هوشمند (اصلاح با LLM)

پنل کلینر می‌تواند به‌صورت اختیاری خروجی OCR را از طریق یک مدل زبانی بزرگ (LLM) عبور دهد تا متن نامفهوم را اصلاح کند — اصلاح کاراکترهای نادرست خوانده‌شده، کلمات شکسته و علائم نگارشی اضافی — ضمن حفظ زبان و معنای اصلی. این برنامه **ترجمه نمی‌کند**. این قابلیت زمانی مفید است که خروجی خام manga-ocr یا Tesseract پرنویز باشد و متن تمیزتری برای ترجمه یا بایگانی بخواهید.

این قابلیت توسط [airllm](https://github.com/lyogavin/Anima/tree/main/air_llm) تأمین می‌شود که با offloading لایه‌به‌لایه به دیسک، اجازه می‌دهد مدل‌های بسیار بزرگی (مثلاً Llama-3-70B) با فقط چند گیگابایت RAM اجرا شوند، به‌بهای کندی تولید توکن.

### فعال‌سازی اصلاح LLM

این قابلیت **به‌صورت پیش‌فرض خاموش است**. ابتدا افزونه اختیاری `[llm]` را نصب کنید:

```bash
pip install pcleaner[llm]
```

سپس آن را برای یک اجرای OCR با پرچم `--use-llm` فعال کنید:

```bash
pcleaner ocr myfolder --output-path=output.txt --use-llm
```

یا آن را به‌صورت دائمی با تنظیم `llm_enabled = True` در بخش `[LLM]` از [پروفایل](#پروفایل‌ها) خود فعال کنید:

```ini
[LLM]
llm_enabled = True
llm_model = meta-llama/Meta-Llama-3-8B-Instruct
llm_max_bubbles_per_prompt = 40
llm_max_new_tokens = 1024
llm_compression =        # خالی بگذارید، یا "4bit" / "8bit"
llm_hf_token =           # برای مدل‌های gated مثل meta-llama/* الزامی است
```

### نحوه کار

1. پنل کلینر OCR را به‌طور معمول اجرا می‌کند و متن هر حباب تشخیص‌داده‌شده را جمع‌آوری می‌کند.
2. متن OCR از حباب‌های متعدد در یک prompt واحد LLM دسته‌بندی می‌شود (چون تولید airllm کند است، دسته‌بندی بسیار سریع‌تر از یک prompt به ازای هر حباب است).
3. LLM یک آرایه JSON از رشته‌های اصلاح‌شده برمی‌گرداند که جایگزین خروجی خام OCR می‌شوند.
4. اگر یک دسته شکست بخورد یا مدل تعداد اشتباهی آیتم برگرداند، متن OCR اصلی برای آن دسته حفظ می‌شود — بنابراین یک دسته بد هرگز کل اجرا را قطع نمی‌کند.

### نکات

- **با طراحی کند است:** airllm لایه‌های مدل را به دیسک offload می‌کند، بنابراین تولید بسیار کندتر از استنتاج معمول GPU است. این بهای اجرای مدل‌های بزرگ با RAM کم است.

- **مدل‌های instruct-tuned** (مثلاً `Meta-Llama-3-8B-Instruct`) به‌شدت توصیه می‌شوند.

- **مدل‌های gated** (مانند مخازن `meta-llama/*`) به یک [توکن Hugging Face](https://huggingface.co/settings/tokens) نیاز دارند. آن را از طریق `llm_hf_token` در پروفایل یا متغیر محیطی `HF_TOKEN` تنظیم کنید.

- **فشرده‌سازی:** تنظیم `llm_compression` روی `4bit` یا `8bit` کوانتیزاسیون بلوکی را برای شتاب تا ~۳ برابر با افت دقت کم فعال می‌کند (نیازمند بسته `bitsandbytes`).

- **GPU توصیه می‌شود:** airllm بر CUDA هدف‌گیری شده است. روی سیستم‌های فقط-CPU ممکن است مدل بارگذاری نشود — در این صورت اجرا به‌طور خودکار به خروجی خام OCR برمی‌گردد.

---

## نمونه‌هایی از حباب‌های پیچیده

| تصویر اصلی | پاک‌شده |
|:--------:|:-------:|
| ![Square bubble raw](https://raw.githubusercontent.com/VoxelCubes/PanelCleaner/master/media/demo_bubbles/square_bubble_raw.png) | ![Square bubble clean](https://raw.githubusercontent.com/VoxelCubes/PanelCleaner/master/media/demo_bubbles/square_bubble_clean.png) |
| ![Handwritten bubble raw](https://raw.githubusercontent.com/VoxelCubes/PanelCleaner/master/media/demo_bubbles/handwritten_bubble_raw.png) | ![Handwritten bubble clean](https://raw.githubusercontent.com/VoxelCubes/PanelCleaner/master/media/demo_bubbles/handwritten_bubble_clean.png) |
| ![Black bubble raw](https://raw.githubusercontent.com/VoxelCubes/PanelCleaner/master/media/demo_bubbles/black_bubble_raw.png) | ![Black bubble clean](https://raw.githubusercontent.com/VoxelCubes/PanelCleaner/master/media/demo_bubbles/black_bubble_clean.png) |
| ![Ray bubble raw](https://raw.githubusercontent.com/VoxelCubes/PanelCleaner/master/media/demo_bubbles/ray_bubble_raw.png) | ![Ray bubble clean](https://raw.githubusercontent.com/VoxelCubes/PanelCleaner/master/media/demo_bubbles/ray_bubble_clean.png) |
| ![Nightmare bubble raw](https://raw.githubusercontent.com/VoxelCubes/PanelCleaner/master/media/demo_bubbles/nightmare_bubble_raw.png) | ![Nightmare bubble clean](https://raw.githubusercontent.com/VoxelCubes/PanelCleaner/master/media/demo_bubbles/nightmare_bubble_clean.png) |
| ![Spikey bubble raw](https://raw.githubusercontent.com/VoxelCubes/PanelCleaner/master/media/demo_bubbles/spikey_bubble_raw.png) | ![Spikey bubble clean](https://raw.githubusercontent.com/VoxelCubes/PanelCleaner/master/media/demo_bubbles/spikey_bubble_clean.png) |
| ![Darkrays bubble raw](https://raw.githubusercontent.com/VoxelCubes/PanelCleaner/master/media/demo_bubbles/darkrays_bubble_raw.png) | ![Darkrays bubble clean](https://raw.githubusercontent.com/VoxelCubes/PanelCleaner/master/media/demo_bubbles/darkrays_bubble_clean.png) |

---

## تشکر و قدردانی

- [Comic Text Detector](https://github.com/dmMaze/comic-text-detector) برای یافتن حباب‌های متنی و تولید ماسک اولیه.

- [Manga OCR](https://github.com/kha-white/manga-ocr) برای تشخیص حباب‌هایی که فقط شامل نمادها یا اعداد هستند،
  و اجرای دستور اختصاصی OCR.

- [Simple Lama Inpainting](https://github.com/enesmsahin/simple-lama-inpainting) برای inpaint کردن حباب‌هایی که نمی‌توان با ماسک پوشاند.
  با استفاده از [مدل fine-tune‌شده توسط dreMaz](https://huggingface.co/dreMaz/AnimeMangaInpainting).

- [airllm](https://github.com/lyogavin/Anima/tree/main/air_llm) برای اجرای مدل‌های زبانی بزرگ با RAM کم از طریق offloading لایه‌ای به دیسک، که در قابلیت اصلاح هوشمند OCR استفاده می‌شود.

---

## پروانه

این پروژه تحت پروانه GNU General Public License v3.0 منتشر شده است — برای جزئیات به
فایل [LICENSE](https://raw.githubusercontent.com/VoxelCubes/PanelCleaner/master/LICENSE) مراجعه کنید.

---

## نقشه راه

- در حال حاضر هیچ قابلیت جدیدی برنامه‌ریزی نشده است.
