import sys
import os
import re
import requests
from bs4 import BeautifulSoup
from ebooklib import epub
from tqdm import tqdm
from colorama import Fore, init

BOOKS = {}
CHAPTER_TITLES = []
BOOK_TITLE = ""
AUTHOR = ""
IMG_PATH = ""

BANNER = """
/==========================\\
||░█▄█░█░█░█▀▀░█▀█░█░█░█▀▄||
||░█░█░█▀▄░█▀▀░█▀▀░█░█░█▀▄||
||░▀░▀░▀░▀░▀▀▀░▀░░░▀▀▀░▀▀░||
\\==========================/
"""

# region crawl

def get_chapter_link(url: str, lst_num: int) -> list:
    
    url_list = []
    
    for i in range(1, lst_num+1):
        
        url1 = f'{url}trang-{i}/#list-chapter'
        res = requests.get(url1)
        
        tqdm.write(Fore.CYAN + f"[+] Fetch {url1}")
        
        if res.status_code != 200:
            break 
        
        soup = BeautifulSoup(res.content, 'html.parser')
        src = soup.find_all('ul', class_="list-chapter")
        
        if not src:
            break
        
        soup = BeautifulSoup(str(src), 'html.parser')
        links = soup.find_all('a')
        
        if not links:  
            break
        
        for link in links:
            href = link['href']
            if href:
                url_list.append(href)
        
    return url_list

def get_content(url):
    global CHAPTER_TITLES
    global BOOKS
    res = requests.get(url).content
    soup = BeautifulSoup(res, 'html.parser')
    
    # remove ad
    for ads in soup.find_all(id=re.compile(r'^ads')):
        ads.decompose()
    
    # get chapter title
    chapter_title = soup.find('a', class_='chapter-title')
    if chapter_title:
        chapter_title = chapter_title.text
    else:
        chapter_title = "unk"
    
    # get content 
    res_wo_ads = soup.prettify()
    soup = BeautifulSoup(res_wo_ads, 'html.parser')
    content = soup.find('div', class_='chapter-c')
    if content:
        content = content.decode_contents()
        CHAPTER_TITLES.append(chapter_title)
        BOOKS[chapter_title] = content

def get_book_title(url):
    global BOOK_TITLE
    res = requests.get(url).content
    soup = BeautifulSoup(res, 'html.parser')
    BOOK_TITLE = soup.find('h3', class_='title')
    if BOOK_TITLE:
        BOOK_TITLE = BOOK_TITLE.text
    else:
        BOOK_TITLE = "unk"
    
def get_author(url):
    global AUTHOR
    try:
        res = requests.get(url).content
        soup = BeautifulSoup(res, 'html.parser')
        AUTHOR = soup.find('a', attrs={'itemprop':'author'})
        if AUTHOR:
            AUTHOR = AUTHOR.text
        else:
            AUTHOR = "unk"    
    except requests.exceptions.RequestException:
        print(Fore.RED + "[+] INVALID URL!!!")
        print(Fore.GREEN + "[+] VALID URL: https://truyenfull.bio/ten-truyen/")
        sys.exit(1)

def make_dict(url, lst_num):
    links = get_chapter_link(url, lst_num)
    
    for link in links:
        tqdm.write(Fore.CYAN + f"[+] Fetch {link}")
        get_content(link)
        
def get_cover_img(url):
    global IMG_PATH
    
    res = requests.get(url).content
    soup = BeautifulSoup(res, 'html.parser')
    img_tag = soup.find('img')
    if img_tag:
        img_src = img_tag['src']
    
    #IMG_PATH = f'{BOOK_TITLE}.jpg'
    
    res = requests.get(img_src)
    if res.status_code == 200:
        with open("test.jpg", 'wb') as f:
            f.write(res.content)
            
        
# endregion

# region tạo epub
def make_chapter(i):
    title = CHAPTER_TITLES[i]
    content = BOOKS[title].strip()
    if not content:
        tqdm.write(Fore.RED + f"[+] ERROR: Chapter {i+1} is empty!")
        content = "<p>No content available</p>"
    chapter = epub.EpubHtml(title=title, file_name=f"chapter{i+1}.xhtml")
    chapter.content = f'<h2>{title}</h2>'+content
    return chapter


def make_epub(url):
    book = epub.EpubBook()
    
    # thêm metadata
    book.set_title(BOOK_TITLE)
    book.set_language("vi")
    book.add_author(AUTHOR)
    
    # Set cover
    cover_image_path = "test.jpg"  # Ensure the image exists in this path
    if os.path.exists(cover_image_path):
        book.set_cover("cover.jpg", open(cover_image_path, 'rb').read())
    else:
        tqdm.write(Fore.RED + f"[+] ERROR: Cover image '{cover_image_path}' not found.")
    
    # tao chuong
    total_chapter = len(BOOKS)
    chapters = []
    
    for i in tqdm(range(total_chapter), desc= "Creating"):
        chapter = make_chapter(i)
        if chapter.content:
            book.add_item(chapter)
            chapters.append(chapter)
        else:
            tqdm.write(Fore.RED + f"[+] ERROR: Empty chapter content detected for {CHAPTER_TITLES[i]}")
            
    
    # add navigation
    if chapters:
        book.toc = chapters
        book.spine = ['nav'] + chapters
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
    
    # save epub
    output_dir = 'books'  # Replace with your desired folder name or path

    # Create the folder if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    safe_title = ''.join(c if c.isalnum() or c in " .-_()" else '_' for c in BOOK_TITLE)
    output_file_path = os.path.join(output_dir, f'{safe_title}.epub')
    
    epub.write_epub(output_file_path, book) 
# endregion

def main(url, lst_num):
    # get info
    get_book_title(url)
    get_cover_img(url)
    get_author(url)
    make_dict(url,lst_num)
    
    # make epub
    make_epub(url)
    

if __name__=="__main__":
    init(autoreset=True)
    print(Fore.MAGENTA + BANNER,end="")
    if len(sys.argv)<3:
        print(Fore.RED + "[+] Usage: mkepub.py <url> <list_chapter_number>")
        sys.exit(1)
    url = sys.argv[1].strip()
    lst_num = int(sys.argv[2].strip())

    main(url, lst_num)
    os.remove("test.jpg")