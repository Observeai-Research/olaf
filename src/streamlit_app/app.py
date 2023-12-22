import logging
import time
import typing

import streamlit as st

from src.constants import MAX_COCKTAIL_ENDPOINTS, CORE_SERVICES, EXPERIMENTAL_SERVICES, HIDE_ST_STYLE
from src.streamlit_app.advanced_usage_ui import show_core_services, get_advanced_usage_params
from src.streamlit_app.datamodel import OlafAdvancedParams, service_config
from src.streamlit_app.utils import (is_port_in_use, get_log_message, stop_running_locust_pids,
                                     prune_db_for_terminated_process, add_locust_pids_to_db, TEST_TYPE_TO_DRIVER_MAP)

logger = logging.getLogger()


def init_streamlit():
    st.set_page_config(page_title="🤖, Olaf", page_icon="🤖")
    st.markdown(HIDE_ST_STYLE, unsafe_allow_html=True)
    st.write("> Some loads are worth melting for. ❄️")
    st.header("🤖: Hi, I am Olaf!")


def start_olaf_session(advanced_params: typing.Dict, resource_args):
    st.session_state["session_requested"] = True
    logger.info(get_log_message("session-requested", test_type))
    if is_port_in_use():
        logger.info(get_log_message("session-failed", "existing session"))
        st.error("another load session in progress. try closing it before proceeding!")
    else:
        with st.spinner("initializing session..."):
            if advanced_params:
                advanced_params = OlafAdvancedParams(**advanced_params)

            test_type_driver = TEST_TYPE_TO_DRIVER_MAP.get(test_type, None)
            assert test_type_driver is not None
            p_ids = test_type_driver(resource_args,
                                     locust_config=service_config.locust_config,
                                     advanced_params=advanced_params,
                                     load_session_name=load_session_name, )

            add_locust_pids_to_db(test_type, p_ids)
            time.sleep(5)

        logger.info(get_log_message("session-started", test_type))


def stop_olaf_session(placeholder_stop_btn, placeholder_link):
    stop_load_btn = placeholder_stop_btn.button("STOP RUNNING LOAD SESSION")
    placeholder_link.markdown(f"The session is running at [link]({'/active_session/'})")
    if stop_load_btn:
        with st.spinner("cleaning up and closing session..."):
            stop_running_locust_pids()
            placeholder_stop_btn.empty()
            placeholder_link.empty()
            # give time to upload results to s3 and die
            time.sleep(5)
        with st.spinner("hold on uploading results to s3 (if configured)..."):
            # give some more time to upload results to s3 and die
            time.sleep(5)
        with st.spinner("pruning process cache for performance..."):
            prune_db_for_terminated_process()


if __name__ == '__main__':
    init_streamlit()

    test_type = st.sidebar.radio("Choose resource to load test.",
                                 options=CORE_SERVICES + EXPERIMENTAL_SERVICES)

    resource_args = None

    if test_type == "Cocktail":
        resource_args = []
        st.info("experimental offering, handle with care!")
        for endpoint_num in range(MAX_COCKTAIL_ENDPOINTS):
            with st.expander(label=f"endpoint-{endpoint_num + 1}", expanded=True and not endpoint_num):
                selected_service = st.selectbox(label="select service", options=["None"] + CORE_SERVICES,
                                                key=endpoint_num)
                if selected_service != "None":
                    service_args = show_core_services(test_type=selected_service,
                                                      is_cocktail=True,
                                                      key=endpoint_num, )
                    resource_args.append(service_args)

    else:
        service_args = show_core_services(test_type)
        resource_args = service_args

    advanced_params = get_advanced_usage_params()

    load_session_name = st.text_input("Load session Name")

    start_session_btn = st.button(f"START LOAD SESSION")

    placeholder_stop_btn = st.empty()
    placeholder_link = st.empty()

    if start_session_btn:
        start_olaf_session(advanced_params, resource_args)

    if st.session_state.get("session_requested", False) is True and is_port_in_use():
        stop_olaf_session(placeholder_stop_btn, placeholder_link)
