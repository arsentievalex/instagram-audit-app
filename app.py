import streamlit as st
from instaloader import Instaloader, Profile
from PIL import Image, ImageChops, ImageDraw, ImageOps
import requests
from io import BytesIO
import plotly.express as px
from collections import Counter


st.set_page_config(
     page_title="Insta Audit App",
     page_icon=":rocket:",
     layout="wide")


def crop_to_circle(im):
    bigsize = (im.size[0] * 3, im.size[1] * 3)
    mask = Image.new('L', bigsize, 0)
    ImageDraw.Draw(mask).ellipse((0, 0) + bigsize, fill=255)
    mask = mask.resize(im.size, Image.ANTIALIAS)
    mask = ImageChops.darker(mask, im.split()[-1])
    im.putalpha(mask)
    return im


def scrape_inst(username, login, password):
    loader = Instaloader()
    #loader.login(login, password)
    loader.load_session_from_file('pawpawart_pl', filename='sessionfile123')
    target_profile = username

    profile = Profile.from_username(loader.context, target_profile)

    num_followers = profile.followers
    user_name = profile.username
    profile_pic = profile.profile_pic_url
    mediacount = profile.mediacount

    posts_list = []
    total_num_likes = 0
    total_num_comments = 0
    total_num_posts = 0
    hashtag_list = []

    for post in profile.get_posts():
        if total_num_posts < 50:
            total_num_likes += post.likes
            total_num_comments += post.comments
            posts_list.append(post)
            hashtag_list.append(post.caption_hashtags)
            total_num_posts += 1


    engagement = round(float(total_num_likes + total_num_comments) / (num_followers * total_num_posts) * 100, 2)
    avg_comments = round(total_num_comments/total_num_posts)
    avg_likes = round(total_num_likes/total_num_posts)


    # clean hashtags list
    hashtags_raw = [', '.join(ele) for ele in hashtag_list]
    hashtags_clean = list(filter(None, hashtags_raw))
    hashtags_str = ", ".join(hashtags_clean)
    hashtags_list = hashtags_str.split(',')


    # create counter objects to count elements
    count_dict = Counter(hashtags_list)
    sorted_dict = sorted(count_dict.items(), key=lambda x: x[1], reverse=True)

    # create final sorted list of hashtags
    hashtags_list_clean = []
    for i in sorted_dict:
        hashtags_list_clean.append(i[0].strip())

    # calculate top 15% hashtags
    most_used_hashtags = round(len(hashtags_list_clean) * 0.15)
    most_used_hashtags_str = ", ".join(hashtags_list_clean[:most_used_hashtags])


    # sort posts by number of likes and comments
    posts_sorted = sorted(posts_list, key=lambda p: p.likes + p.comments, reverse=True)
    best_post1 = posts_sorted[0].url
    best_post2 = posts_sorted[1].url
    best_post3 = posts_sorted[2].url

    worst_post1 = posts_sorted[-1].url
    worst_post2 = posts_sorted[-2].url
    worst_post3 = posts_sorted[-3].url


    # create image objects
    response = requests.get(profile_pic)
    profile_img = Image.open(BytesIO(response.content)).convert('RGBA')
    profile_round = crop_to_circle(profile_img)

    response2 = requests.get(best_post1)
    best1 = Image.open(BytesIO(response2.content))
    best1 = ImageOps.contain(best1, (200, 200))

    response3 = requests.get(worst_post1)
    worst1 = Image.open(BytesIO(response3.content))
    worst1 = ImageOps.contain(worst1, (200, 200))

    response4 = requests.get(worst_post2)
    worst2 = Image.open(BytesIO(response4.content))
    worst2 = ImageOps.contain(worst2, (200, 200))

    response5 = requests.get(worst_post3)
    worst3 = Image.open(BytesIO(response5.content))
    worst3 = ImageOps.contain(worst3, (200, 200))

    response6 = requests.get(best_post2)
    best2 = Image.open(BytesIO(response6.content))
    best2 = ImageOps.contain(best2, (200, 200))

    response7 = requests.get(best_post3)
    best3 = Image.open(BytesIO(response7.content))
    best3 = ImageOps.contain(best3, (200, 200))

    st.image(profile_round, width=100)
    st.write('User name: {}'.format(str(user_name)))
    st.write(':man-woman-girl-boy: Number of followers: {:,}'.format(num_followers))
    st.write('🔍 Number of posts analyzed: {:,} (out of {:,})'.format(total_num_posts, mediacount))
    st.write(':chart_with_upwards_trend: Engagement rate: {}%'.format(str(engagement)))
    st.write(':heart: Average number of likes: {:,}'.format(avg_likes))
    st.write(':writing_hand: Average number of comments: {:,}'.format(avg_comments))
    st.write(':hash: Most used hashtags: {}'.format(most_used_hashtags_str))


    # define ER benchmark based on the number of followers
    if int(num_followers) <= 5000:
        benchmark = 5.6
        benchmark_num_fol = "<5k followers"
    elif int(num_followers) > 5000 and int(num_followers) <= 20000:
        benchmark = 2.43
        benchmark_num_fol = "5k-20k followers"
    elif int(num_followers) > 20000 and int(num_followers) <= 100000:
        benchmark = 2.15
        benchmark_num_fol = "20k-100k followers"
    elif int(num_followers) > 100000 and int(num_followers) <= 1000000:
        benchmark = 2.05
        benchmark_num_fol = "100k-1m followers"
    elif int(num_followers) > 1000000:
        benchmark = 1.97
        benchmark_num_fol = ">1m followers"

    # display text whether the ER is greater or smaller then benchmark
    if engagement > benchmark:
        dif = round(engagement-benchmark, 2)
        markdown = '<span>**The engagement rate of {} is </span><span style = "color:Green;">greater than benchmark </span>' \
                   '<span>for profiles with {} by {}**</span>'.format(user_name.capitalize(), benchmark_num_fol, str(dif) + '%')
        st.markdown(markdown, unsafe_allow_html=True)
    elif engagement < benchmark:
        dif = round(benchmark-engagement, 2)
        markdown = '<span>**The engagement rate of {} is </span><span style = "color:Red;">smaller than benchmark </span>' \
                   '<span>for profiles with {} by {}**</span>'.format(user_name.capitalize(), benchmark_num_fol, str(dif) + '%')
        st.markdown(markdown, unsafe_allow_html=True)

    # create bar chart with ER vs benchmark
    label_1 = str(user_name).capitalize()
    label_2 = "Benchmark {}".format(benchmark_num_fol)
    fig = px.bar(x=[label_1, label_2], y=[engagement, benchmark], color=['#CA38A7', '#FFAF4C'],
                 title="Engagement Rate vs Benchmark %", labels=dict(x="Category", y="ER"),
                 color_discrete_map="identity")
    fig.update_layout(yaxis={'title': ''}, xaxis={'title': ''})

    # display the chart
    st.plotly_chart(fig)

    best_container = st.container()
    worst_container = st.container()

    with best_container:
        # show 3 best and worst performing posts
        st.write('**Best performing posts:**')

        col1, col2, col3 = st.columns(3)

        with col1:
            st.image(best1)

        with col2:
            st.image(best2)

        with col3:
            st.image(best3)

    with worst_container:
        # show 3 best and worst performing posts
        st.write('**Worst performing posts:**')

        col1, col2, col3 = st.columns(3)

        with col1:
            st.image(worst1)
        with col2:
            st.image(worst2)
        with col3:
            st.image(worst3)

    #loader.save_session_to_file(filename='sessionfile123')


st.title('Welcome to Instagram Audit App!')
st.subheader("This app lets you analyze basic Instagram metrics such as engagement rate, hashtags and most/least popular posts of any Instagram profile")

with st.sidebar:
    st.write('**Log in to your Instagram profile in order to use the app**')
    login = st.text_input('Username')
    password = st.text_input('Password', type='password')
    st.warning('Note: the app does not store your Instagram credentials, logging in is required by the Instaloader library to scrape the Instagram data.'
             'For more details, please refer to the source code on GitHub.', icon="⚠")

user_input = st.text_input(' ', placeholder='Enter Instagram username')
run_button = st.button('Run')


# show example profile analysis
with st.expander("See example"):
    st.write("")
    st.image('https://i.postimg.cc/2SZ3XXmq/profile-pic.png')
    st.write('User name: zuck')
    st.write(':man-woman-girl-boy: Number of followers: 10,200,185')
    st.write('🔍 Number of posts analyzed: 50 (out of 243)')
    st.write(':chart_with_upwards_trend: Engagement rate: 1.72%')
    st.write(':heart: Average number of likes: 169,835')
    st.write(':writing_hand: Average number of comments: 5,696')
    st.write(':hash: Most used hashtags: ')

    markdown = '<span>**The engagement rate of zuck is </span><span style = "color:Red;">smaller than benchmark </span>' \
               '<span>for profiles with >1m followers by 0.25%**</span>'
    st.markdown(markdown, unsafe_allow_html=True)

    # create bar chart with ER vs benchmark
    label_1 = 'zuck'
    label_2 = "Benchmark "
    fig = px.bar(x=[label_1, label_2], y=[1.72, 1.97], color=['#CA38A7', '#FFAF4C'],
                 title="Engagement Rate vs Benchmark %", labels=dict(x="Category", y="ER"),
                 color_discrete_map="identity")
    fig.update_layout(yaxis={'title': ''}, xaxis={'title': ''})

    # display the chart
    st.plotly_chart(fig)

    best_container = st.container()
    worst_container = st.container()

    with best_container:
        # show 3 best performing posts
        st.write('**Best performing posts:**')
        col1, col2, col3 = st.columns(3)
        with col1:
            st.image('https://i.postimg.cc/cCCL7FXL/best1.jpg')
        with col2:
            st.image('https://i.postimg.cc/Njmfx97m/best2.jpg')
        with col3:
            st.image('https://i.postimg.cc/mrSL0vnr/best3.jpg')

    with worst_container:
        # show 3 worst performing posts
        st.write('**Worst performing posts:**')
        col1, col2, col3 = st.columns(3)
        with col1:
            st.image('https://i.postimg.cc/x8BnvnX6/worst1.jpg')
        with col2:
            st.image('https://i.postimg.cc/ncQHHjWg/worst2.jpg')
        with col3:
            st.image('https://i.postimg.cc/cLR03q0c/worst3.jpg')



# run the scrape function
if run_button and len(login) == 0 or run_button and len(password) == 0:
    st.warning('Please enter your Instagram credentials to use the app')

elif run_button and len(login) > 0 and len(password) > 0:
    st.write(" ")
    with st.spinner("Auditing Instagram profile...:hourglass_flowing_sand: (it may take up to 2-3 mins)"):
        try:
            scrape_inst(user_input, login, password)
        except Exception as e:
            st.error('Oops...something went wrong. Please try again!', icon="🚨")
            st.error('Error message: {}'.format(e))










